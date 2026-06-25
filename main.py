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
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("--timezone=America/New_York")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # 伪装自动化特征
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    wait = WebDriverWait(driver, 20)

    try:
        # 1. 预先注入 Cookie 绕过隐私弹窗
        driver.get("https://eternalzero.cloud/")
        driver.add_cookie({'name': 'cookies_accepted', 'value': 'true', 'domain': '.eternalzero.cloud'})
        driver.add_cookie({'name': 'notice_gdpr_prefs', 'value': '0:1', 'domain': '.eternalzero.cloud'})
        
        # 2. 登录流程
        driver.get("https://eternalzero.cloud/login")
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()

        # 3. 详情页处理
        driver.get("https://eternalzero.cloud/servers/5541/info")
        print("等待页面加载...")
        time.sleep(15) # 给插件初始化和页面渲染留出时间
        
        # 强制清理残留遮罩
        driver.execute_script("document.querySelectorAll('.fc-dialog-overlay, .modal-backdrop').forEach(e => e.style.display='none')")
        
        # 4. 人机验证与点击
        if "h-captcha" in driver.page_source:
            captcha_box = driver.find_element(By.CSS_SELECTOR, ".h-captcha")
            driver.execute_script("arguments[0].scrollIntoView();", captcha_box)
            print("等待插件自动处理验证...")
            time.sleep(10)

        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        
        time.sleep(5)
        # 动态调整截图高度
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
