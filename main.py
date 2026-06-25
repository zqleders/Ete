import os
import time
import requests
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

def light_clear(driver):
    """精简版清理：不再使用监听，只进行一次性清理"""
    try:
        driver.execute_script("""
            var buttons = document.querySelectorAll('button');
            buttons.forEach(function(btn) {
                if (btn.innerText.match(/Do not consent|Reject|Close/i)) btn.click();
            });
            var masks = document.querySelectorAll('.fc-dialog-overlay, .modal-backdrop');
            masks.forEach(function(m) { m.style.display = 'none'; });
            document.body.style.overflow = 'auto';
        """)
    except: pass

def run_browser():
    chrome_options = Options()
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    chrome_options.add_argument("--window-size=1280,720") # 调低分辨率以节省内存
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu") # 额外优化
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://eternalzero.cloud/login")
        time.sleep(3)
        light_clear(driver)
        
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()

        driver.get("https://eternalzero.cloud/servers/5541/info")
        time.sleep(5) 
        light_clear(driver)
        
        # hCaptcha 逻辑
        if "h-captcha" in driver.page_source:
            sitekey = driver.execute_script('return document.querySelector(".h-captcha").getAttribute("data-sitekey")')
            resp = requests.post("https://api.nopecha.com/v1", json={"key": NOPECHA_KEY, "type": "hcaptcha", "sitekey": sitekey, "url": driver.current_url}).json()
            if resp.get('status') == 'success':
                driver.execute_script(f'document.querySelector("[name=h-captcha-response]").value = "{resp["data"]}";')
                driver.execute_script('hcaptcha.execute();')
        
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
