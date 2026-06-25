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
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

def solve_hcaptcha(driver):
    """严格遵循 NopeCHA API 文档逻辑"""
    print("正在检测人机验证...")
    captcha_elements = driver.find_elements(By.CLASS_NAME, "h-captcha")
    if not captcha_elements: return False
    
    sitekey = captcha_elements[0].get_attribute("data-sitekey")
    payload = {"key": NOPECHA_KEY, "type": "hcaptcha", "sitekey": sitekey, "url": driver.current_url}
    
    # POST 提交任务
    resp = requests.post("https://api.nopecha.com/v1/solve", json=payload)
    if resp.status_code != 200: return False
    task_id = resp.json().get("data")
    
    # GET 轮询状态
    for _ in range(30):
        time.sleep(3)
        res = requests.get(f"https://api.nopecha.com/v1/status?key={NOPECHA_KEY}&id={task_id}").json()
        if res.get("status") == "solved":
            token = res.get("data")
            driver.execute_script(f'document.querySelector("[name=h-captcha-response]").value = "{token}";')
            driver.execute_script("hcaptcha.callback();")
            print("人机验证通过。")
            return True
    return False

def handle_all_tasks(driver):
    """处理隐私弹窗、看广告、人机验证的全套逻辑"""
    # 1. 隐私对话框
    consent_btns = driver.find_elements(By.CSS_SELECTOR, "button.fc-cta-consent")
    for btn in consent_btns:
        if btn.is_displayed():
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
            
    # 2. 看广告逻辑
    ad_btns = driver.find_elements(By.CSS_SELECTOR, "button.fc-rewarded-ad-button")
    if ad_btns and ad_btns[0].is_displayed():
        print("发现广告，开始观看...")
        driver.execute_script("arguments[0].click();", ad_btns[0])
        time.sleep(30) # 强制等待广告完成
        
        # 修复：确保关闭按钮被点击
        try:
            close_btn = driver.find_element(By.ID, "dismiss-button-element")
            if close_btn.is_displayed():
                driver.execute_script("arguments[0].click();", close_btn)
                print("已执行点击关闭广告按钮。")
            time.sleep(2)
        except Exception as e:
            print(f"关闭广告按钮点击失败: {e}")
            
    # 3. 处理人机验证
    solve_hcaptcha(driver)

def run_browser():
    chrome_options = Options()
    chrome_options.add_argument("--window-position=0,0")
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", fix_hairline=True)
    wait = WebDriverWait(driver, 20)

    try:
        # 1. 登录
        driver.get("https://eternalzero.cloud/login")
        handle_all_tasks(driver)
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()
        time.sleep(10)

        # 2. Info页操作
        driver.get("https://eternalzero.cloud/servers/5541/info")
        time.sleep(10)
        handle_all_tasks(driver)
        
        # 3. 续费
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        
        time.sleep(5)
        driver.save_screenshot("result.png")
        send_telegram("✅ 所有任务完成（广告、验证、续费）。", "result.png")
    except Exception as e:
        driver.save_screenshot("error.png")
        send_telegram(f"❌ 自动化失败: {str(e)}", "error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
