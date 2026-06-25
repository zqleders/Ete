import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

# 环境配置
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
    """根据官方文档：POST 提交任务 -> GET 轮询状态 -> 注入响应"""
    print("正在检测人机验证...")
    # 1. 查找验证码容器并提取必要参数
    captcha_elements = driver.find_elements(By.CLASS_NAME, "h-captcha")
    if not captcha_elements:
        print("未发现人机验证，跳过。")
        return False
    
    sitekey = captcha_elements[0].get_attribute("data-sitekey")
    url = driver.current_url
    
    # 2. 调用 POST 接口提交任务 (Reference: #postHcaptcha)
    print(f"提交任务到 NopeCHA，Sitekey: {sitekey}")
    payload = {"key": NOPECHA_KEY, "type": "hcaptcha", "sitekey": sitekey, "url": url}
    resp = requests.post("https://api.nopecha.com/v1/solve", json=payload)
    if resp.status_code != 200:
        print(f"任务提交失败: {resp.text}")
        return False
    
    task_id = resp.json().get("data")
    print(f"任务已提交，ID: {task_id}，开始轮询结果...")

    # 3. 调用 GET 接口轮询状态 (Reference: #getHcaptcha)
    for _ in range(30):
        time.sleep(3)
        res = requests.get(f"https://api.nopecha.com/v1/status?key={NOPECHA_KEY}&id={task_id}").json()
        status = res.get("status")
        if status == "solved":
            token = res.get("data")
            print("验证码识别成功，正在注入...")
            # 注入 Token 并触发回调
            driver.execute_script(f'document.querySelector("[name=h-captcha-response]").value = "{token}";')
            driver.execute_script("hcaptcha.callback();")
            return True
        elif status == "failed":
            print("验证码识别失败。")
            return False
    print("轮询超时。")
    return False

def clean_ads(driver):
    """清理页面广告"""
    # 处理隐私弹窗
    for btn in driver.find_elements(By.CSS_SELECTOR, "button.fc-cta-consent"):
        if btn.is_displayed(): driver.execute_script("arguments[0].click();", btn)
    # 处理激励广告
    ad_btns = driver.find_elements(By.CSS_SELECTOR, "button.fc-rewarded-ad-button")
    if ad_btns and ad_btns[0].is_displayed():
        driver.execute_script("arguments[0].click();", ad_btns[0])
        time.sleep(30)
        close_btn = driver.find_elements(By.ID, "dismiss-button-element")
        if close_btn: driver.execute_script("arguments[0].click();", close_btn[0])

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
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()
        time.sleep(10)

        # 2. 访问 Info 页
        driver.get("https://eternalzero.cloud/servers/5541/info")
        time.sleep(10)
        
        # 3. 处理广告
        clean_ads(driver)
        
        # 4. 严格按照 NopeCHA 文档处理人机验证
        solve_hcaptcha(driver)
        
        # 5. 续费
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        
        time.sleep(5)
        driver.save_screenshot("result.png")
        send_telegram("✅ 自动续费成功！", "result.png")
        
    except Exception as e:
        driver.save_screenshot("error.png")
        send_telegram(f"❌ 自动化失败: {str(e)}", "error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
