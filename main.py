import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

# 配置
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
NOPECHA_KEY = os.environ.get("NOPECHA_KEY") 

def get_captcha_token(sitekey, url):
    """根据官方文档使用 GET/POST 配合获取 Token"""
    # 1. 提交任务
    submit_url = "https://api.nopecha.com/v1/solve"
    payload = {
        "key": NOPECHA_KEY,
        "type": "hcaptcha",
        "sitekey": sitekey,
        "url": url,
    }
    resp = requests.post(submit_url, json=payload)
    if resp.status_code != 200: return None
    task_id = resp.json().get("data")
    
    # 2. 轮询获取结果 (文档规范)
    result_url = f"https://api.nopecha.com/v1/status?key={NOPECHA_KEY}&id={task_id}"
    for _ in range(20): # 等待约 60 秒
        time.sleep(3)
        res = requests.get(result_url).json()
        if res.get("status") == "solved":
            return res.get("data")
    return None

def clear_all_ads(driver):
    """循环清理所有弹窗和广告"""
    print("清理页面广告中...")
    for _ in range(5):
        # 处理隐私弹窗
        btns = driver.find_elements(By.CSS_SELECTOR, "button.fc-cta-consent")
        if btns and btns[0].is_displayed():
            driver.execute_script("arguments[0].click();", btns[0])
            time.sleep(1)
        
        # 处理激励广告
        ad_btns = driver.find_elements(By.CSS_SELECTOR, "button.fc-rewarded-ad-button")
        if ad_btns and ad_btns[0].is_displayed():
            driver.execute_script("arguments[0].click();", ad_btns[0])
            time.sleep(30) # 强制等待广告完成
            close = driver.find_elements(By.ID, "dismiss-button-element")
            if close: driver.execute_script("arguments[0].click();", close[0])
            time.sleep(2)
        else:
            break

def run_browser():
    chrome_options = Options()
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless=new")
    
    driver = webdriver.Chrome(options=chrome_options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", fix_hairline=True)

    try:
        driver.get("https://eternalzero.cloud/servers/5541/info")
        # 1. 先去广告
        clear_all_ads(driver)
        
        # 2. 提取并解决验证码
        captcha_el = driver.find_element(By.CLASS_NAME, "h-captcha")
        sitekey = captcha_el.get_attribute("data-sitekey")
        
        print("正在调用 NopeCHA API 获取验证结果...")
        token = get_captcha_token(sitekey, driver.current_url)
        
        if token:
            # 注入 Token
            driver.execute_script(f'document.querySelector("[name=h-captcha-response]").value = "{token}";')
            # 触发提交
            driver.execute_script("hcaptcha.execute();") 
            print("验证码已注入并提交。")
        
        # 3. 点击续费
        renew_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "renew-button")))
        renew_btn.click()
        
        time.sleep(5)
        driver.save_screenshot("result.png")
        print("操作完成。")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
