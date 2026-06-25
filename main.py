import os
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 获取环境配置
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
NOPECHA_KEY = os.environ.get("NOPECHA_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(msg, image_path=None):
    if not TELEGRAM_BOT_TOKEN: return
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"
    try:
        requests.post(f"{base_url}sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                requests.post(f"{base_url}sendPhoto", data={"chat_id": TELEGRAM_CHAT_ID}, files={"photo": f})
    except: pass

def robust_clear_popups(driver):
    """最强清理：循环监控并消除遮罩"""
    # 执行一段 JS 脚本，在页面内持续监测并自动点击拒绝
    driver.execute_script("""
        function clearAll() {
            // 尝试点击所有带有“拒绝”意义的按钮
            var buttons = document.querySelectorAll('button');
            buttons.forEach(function(btn) {
                if (btn.innerText.match(/Do not consent|Reject|Close|Manage options/i)) {
                    btn.click();
                }
            });
            // 暴力隐藏所有遮罩层
            var masks = document.querySelectorAll('.fc-dialog-overlay, .modal-backdrop, .overlay, #privacy-modal');
            masks.forEach(function(m) { m.style.display = 'none'; });
            document.body.style.overflow = 'auto';
        }
        // 执行一次
        clearAll();
        // 绑定到页面变化事件，确保后面跳出的也能被干掉
        window.addEventListener('DOMNodeInserted', clearAll);
    """)

def run_browser():
    chrome_options = Options()
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        # 1. 登录
        driver.get("https://eternalzero.cloud/login")
        robust_clear_popups(driver) # 开启监控
        time.sleep(3)
        
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()

        # 2. 详情页
        driver.get("https://eternalzero.cloud/servers/5541/info")
        time.sleep(5) 
        robust_clear_popups(driver) # 确保遮罩不挡住按钮
        
        # 处理 hCaptcha
        if "h-captcha" in driver.page_source:
            print("发现验证码，准备调用 API...")
            sitekey = driver.execute_script('return document.querySelector(".h-captcha").getAttribute("data-sitekey")')
            resp = requests.post("https://api.nopecha.com/v1", json={"key": NOPECHA_KEY, "type": "hcaptcha", "sitekey": sitekey, "url": driver.current_url}).json()
            if resp.get('status') == 'success':
                driver.execute_script(f'document.querySelector("[name=h-captcha-response]").value = "{resp["data"]}";')
                driver.execute_script('hcaptcha.execute();')
        
        # 3. 触发续费
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        
        time.sleep(5)
        driver.save_screenshot("result.png")
        send_telegram("✅ 操作尝试完成。", "result.png")

    except Exception as e:
        driver.save_screenshot("error.png")
        send_telegram(f"❌ 自动化失败: {str(e)}", "error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
