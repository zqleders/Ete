import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

# 获取环境配置
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
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

def run_browser():
    chrome_options = Options()
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    chrome_options.add_argument(f'--load-extension={os.path.abspath("./extension")}')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=en-US")
    
    driver = webdriver.Chrome(options=chrome_options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", fix_hairline=True)
    wait = WebDriverWait(driver, 20)

    try:
        # 1. 登录
        driver.get("https://eternalzero.cloud/login")
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()

        # 2. 详情页
        driver.get("https://eternalzero.cloud/servers/5541/info")
        print("等待页面渲染...")
        time.sleep(15) 
        
        # 3. 轮询检测验证码是否已完成
        # 插件完成验证后，页面通常会向 textarea 写入一个 response 字符串
        print("检测人机验证状态...")
        max_retries = 10
        for i in range(max_retries):
            # 检查是否有隐藏的 response 字段被填充
            response_field = driver.execute_script('return document.querySelector("[name=h-captcha-response]").value')
            if response_field and len(response_field) > 10:
                print("验证码已自动通过！")
                break
            else:
                print(f"等待验证码填充中... ({i+1}/{max_retries})")
                time.sleep(5)
        
        # 4. 点击续费
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        
        time.sleep(5)
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, total_height)
        driver.save_screenshot("result.png")
        send_telegram("✅ 操作尝试完成。", "result.png")

    except Exception as e:
        driver.save_screenshot("error.png")
        send_telegram(f"❌ 自动化失败: {str(e)}", "error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
