import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# GitHub Secrets 获取
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

def handle_privacy_popup(driver, wait):
    """检测并点击隐私弹窗的通用函数"""
    try:
        # 等待弹窗出现，设置极短超时时间以避免拖慢流程
        popup_wait = WebDriverWait(driver, 5)
        do_not_consent_btn = popup_wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Do not consent')]")))
        do_not_consent_btn.click()
        print("检测到隐私弹窗，已点击 Do not consent")
        time.sleep(1) # 点击后等待弹窗消失
    except:
        pass # 没找到弹窗则忽略

def run_browser():
    chrome_options = Options()
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    chrome_options.add_argument(f'--load-extension={os.path.abspath("./extension")}')
    chrome_options.add_argument("--window-size=1920,1080") # 高清分辨率
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 25)

    try:
        # 1. 访问登录页
        driver.get("https://eternalzero.cloud/login")
        handle_privacy_popup(driver, wait) # 首次加载检测
        
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()

        # 2. 访问服务器列表
        driver.get("https://eternalzero.cloud/servers/list")
        handle_privacy_popup(driver, wait) # 页面跳转后再次检测
        
        if "5541" not in driver.page_source:
            raise Exception("登录成功但未在列表中发现服务器 5541")

        # 3. 访问续费页
        driver.get("https://eternalzero.cloud/servers/5541/info")
        handle_privacy_popup(driver, wait) # 页面跳转后再次检测
        
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        renew_btn.click()
        
        time.sleep(5)
        # 获取页面完整高度并调整窗口以截图完整信息
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, total_height)
        driver.save_screenshot("result.png")
        send_telegram("✅ 服务器续费请求已成功发送。", "result.png")

    except Exception as e:
        driver.save_screenshot("error.png")
        send_telegram(f"❌ 自动化失败: {str(e)}", "error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
