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

def run_browser():
    chrome_options = Options()
    # 1. 设置代理（必须匹配 main.yml 中的端口）
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    # 2. 加载本地插件目录
    chrome_options.add_argument(f'--load-extension={os.path.abspath("./extension")}')
    # 无头模式适配（如果插件在 headless 下失效，可尝试移除此行或使用 --headless=new）
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 25)

    try:
        # --- 登录流程 ---
        driver.get("https://eternalzero.cloud/login")
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        # 鲁棒性点击登录
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()

        # --- 隐私处理 ---
        try:
            privacy_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]")))
            privacy_btn.click()
        except:
            pass

        # --- 检查服务器 ---
        driver.get("https://eternalzero.cloud/servers/list")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        if "5541" not in driver.page_source:
            raise Exception("登录成功但未在列表中发现服务器 5541")

        # --- 续费操作 ---
        driver.get("https://eternalzero.cloud/servers/5541/info")
        
        # 等待人机验证被插件自动处理，然后点击 Renew
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        renew_btn.click()
        
        # 等待操作结果
        time.sleep(5)
        driver.save_screenshot("result.png")
        send_telegram("✅ 服务器续费请求已成功发送。", "result.png")

    except Exception as e:
        driver.save_screenshot("error.png")
        send_telegram(f"❌ 自动化失败: {str(e)}", "error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
