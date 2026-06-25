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
    """检测并移除隐私弹窗及覆盖层"""
    # 1. 尝试点击弹窗按钮
    try:
        popup_wait = WebDriverWait(driver, 5)
        btn = popup_wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Do not consent')]")))
        btn.click()
        print("检测到隐私弹窗，已点击 Do not consent")
        time.sleep(1)
    except:
        pass
    
    # 2. 强制移除任何潜在的覆盖层遮罩
    try:
        driver.execute_script("""
            var overlay = document.querySelector('.fc-dialog-overlay');
            if (overlay) overlay.style.display = 'none';
            var dialog = document.querySelector('.fc-dialog-container');
            if (dialog) dialog.style.display = 'none';
            document.body.style.overflow = 'auto';
        """)
    except:
        pass

def run_browser():
    chrome_options = Options()
    # 代理设置
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    # 加载本地插件
    chrome_options.add_argument(f'--load-extension={os.path.abspath("./extension")}')
    # 高清分辨率与无头模式
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 25)

    try:
        # 1. 登录流程
        driver.get("https://eternalzero.cloud/login")
        handle_privacy_popup(driver, wait)
        
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()

        # 2. 列表页处理
        driver.get("https://eternalzero.cloud/servers/list")
        handle_privacy_popup(driver, wait)
        
        if "5541" not in driver.page_source:
            raise Exception("登录成功但未在列表中发现服务器 5541")

        # 3. 详情页处理 (Renew 操作)
        driver.get("https://eternalzero.cloud/servers/5541/info")
        handle_privacy_popup(driver, wait)
        
        # 使用 JS 强制点击，确保绕过遮罩
        renew_btn = wait.until(EC.presence_of_element_located((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        
        time.sleep(5)
        # 获取完整页面并截图
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
