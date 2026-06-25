import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(msg, image_path=None):
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"
    requests.post(f"{base_url}sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            requests.post(f"{base_url}sendPhoto", data={"chat_id": TELEGRAM_CHAT_ID}, files={"photo": f})

def handle_privacy_popup(driver):
    try:
        # 统一处理所有弹窗
        driver.execute_script("""
            var buttons = Array.from(document.querySelectorAll('button'));
            buttons.forEach(function(btn) {
                if(btn.innerText.includes('Do not consent') || btn.innerText.includes('Reject')) btn.click();
            });
            var selectors = ['.fc-dialog-overlay', '.fc-dialog-container', '.modal-backdrop'];
            selectors.forEach(function(s) {
                var el = document.querySelector(s);
                if (el) el.style.display = 'none';
            });
            document.body.style.overflow = 'auto';
        """)
    except: pass

def run_browser():
    chrome_options = Options()
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    chrome_options.add_argument(f'--load-extension={os.path.abspath("./extension")}')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 30)

    try:
        # 1. 登录
        driver.get("https://eternalzero.cloud/login")
        time.sleep(5) # 给插件启动预留更多时间
        handle_privacy_popup(driver)
        
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()

        # 2. 列表
        driver.get("https://eternalzero.cloud/servers/list")
        time.sleep(5)
        
        # 3. 详情页处理
        driver.get("https://eternalzero.cloud/servers/5541/info")
        time.sleep(10) # 关键：给 hCaptcha 和插件加载预留足够时间
        handle_privacy_popup(driver)
        
        # 点击 Renew 按钮
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        
        time.sleep(8) # 等待验证码自动触发后的响应
        
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, total_height)
        driver.save_screenshot("result.png")
        send_telegram("✅ 操作尝试完成，请查看截图确认状态。", "result.png")

    except Exception as e:
        driver.save_screenshot("error.png")
        send_telegram(f"❌ 自动化失败: {str(e)}", "error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
