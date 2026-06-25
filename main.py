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

def handle_privacy_popup(driver):
    """更激进的遮罩清理：每调用一次都会尝试点击并移除 DOM"""
    try:
        # 1. 点击所有可能的拒绝按钮（通过不同文本尝试）
        buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Do not consent') or contains(., 'Reject') or contains(., 'Close')]")
        for btn in buttons:
            if btn.is_displayed():
                btn.click()
                time.sleep(1)
        
        # 2. 暴力移除所有弹窗层和遮罩
        driver.execute_script("""
            var selectors = ['.fc-dialog-overlay', '.fc-dialog-container', '#privacy-modal', '.modal-backdrop', '.fade', '.show'];
            selectors.forEach(function(s) {
                var el = document.querySelector(s);
                if (el) el.style.display = 'none';
            });
            document.body.style.overflow = 'auto';
        """)
    except Exception as e:
        pass

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
    wait = WebDriverWait(driver, 25)

    try:
        # 1. 登录流程
        driver.get("https://eternalzero.cloud/login")
        # 登录页特殊处理：等待页面稳定后多触发一次清理
        time.sleep(3) 
        handle_privacy_popup(driver)
        
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()

        # 2. 列表页处理
        driver.get("https://eternalzero.cloud/servers/list")
        time.sleep(2)
        handle_privacy_popup(driver)
        
        if "5541" not in driver.page_source:
            raise Exception("登录成功但未在列表中发现服务器 5541")

        # 3. 详情页处理
        driver.get("https://eternalzero.cloud/servers/5541/info")
        time.sleep(3)
        handle_privacy_popup(driver)
        
        # 执行点击
        renew_btn = wait.until(EC.presence_of_element_located((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        
        time.sleep(5)
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
