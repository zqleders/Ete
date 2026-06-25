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
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram 配置缺失，无法发送消息。")
        return
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"
    try:
        requests.post(f"{base_url}sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                requests.post(f"{base_url}sendPhoto", data={"chat_id": TELEGRAM_CHAT_ID}, files={"photo": f})
    except Exception as e:
        print(f"发送 Telegram 失败: {e}")

def solve_hcaptcha(driver):
    print("开始调用 NopeCHA API...")
    sitekey = driver.execute_script('return document.querySelector(".h-captcha").getAttribute("data-sitekey")')
    page_url = driver.current_url
    
    resp = requests.post("https://api.nopecha.com/v1", json={
        "key": NOPECHA_KEY,
        "type": "hcaptcha",
        "sitekey": sitekey,
        "url": page_url
    }).json()
    
    print(f"NopeCHA 返回结果: {resp}")
    
    if resp.get('status') == 'success':
        token = resp['data']
        driver.execute_script(f'document.querySelector("[name=h-captcha-response]").value = "{token}";')
        driver.execute_script('hcaptcha.execute();')
        print("Token 注入成功")
    else:
        raise Exception(f"NopeCHA API 识别失败: {resp}")

def run_browser():
    print("启动浏览器...")
    chrome_options = Options()
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://eternalzero.cloud/login")
        print("已打开登录页")
        
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()
        print("已点击登录")
        
        driver.get("https://eternalzero.cloud/servers/5541/info")
        print("已跳转详情页，等待验证码...")
        
        # 检查是否有验证码
        time.sleep(5)
        if "h-captcha" in driver.page_source:
            solve_hcaptcha(driver)
        
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        print("已触发续费")
        
        time.sleep(5)
        driver.save_screenshot("result.png")
        send_telegram("✅ 操作尝试完成。", "result.png")

    except Exception as e:
        print(f"发生错误: {e}")
        driver.save_screenshot("error.png")
        send_telegram(f"❌ 自动化失败: {str(e)}", "error.png")
    finally:
        driver.quit()
        print("浏览器已关闭")

if __name__ == "__main__":
    run_browser()
