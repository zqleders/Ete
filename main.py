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

def handle_privacy_consent(driver):
    """专门处理 fc-consent-root 隐私弹窗的逻辑"""
    try:
        # 使用 CSS 选择器直接定位“同意”按钮
        consent_btn = driver.find_elements(By.CSS_SELECTOR, "button.fc-cta-consent")
        if consent_btn and consent_btn[0].is_displayed():
            print("检测到隐私对话框，点击“同意”按钮...")
            driver.execute_script("arguments[0].click();", consent_btn[0])
            time.sleep(3) # 等待遮罩层完全移除
            return True
    except Exception as e:
        print(f"处理隐私弹窗时发生异常: {e}")
    return False

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
        # 1. 登录流程
        driver.get("https://eternalzero.cloud/login")
        time.sleep(10) # 给弹窗弹出留足时间
        handle_privacy_consent(driver)
        
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()
        time.sleep(5)

        # 2. 详情页处理
        driver.get("https://eternalzero.cloud/servers/5541/info")
        print("等待详情页渲染...")
        time.sleep(15) 
        
        # 再次检测，防止跳出新的隐私框
        handle_privacy_consent(driver)
        
        # 3. 验证人机状态
        print("检测人机验证状态...")
        for i in range(10):
            response_field = driver.execute_script('return document.querySelector("[name=h-captcha-response]").value')
            if response_field and len(response_field) > 10:
                print("验证码已通过")
                break
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
