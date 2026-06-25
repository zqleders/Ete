import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 获取 Secrets
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
NOPECHA_KEY = os.environ.get("NOPECHA_KEY") 

def solve_hcaptcha(driver):
    """通过 API 获取 Token 并注入"""
    # 1. 获取网页上的 Sitekey 和 URL
    sitekey = driver.execute_script('return document.querySelector(".h-captcha").getAttribute("data-sitekey")')
    page_url = driver.current_url
    
    # 2. 调用 NopeCHA API
    resp = requests.post("https://api.nopecha.com/v1", json={
        "key": NOPECHA_KEY,
        "type": "hcaptcha",
        "sitekey": sitekey,
        "url": page_url
    }).json()
    
    if resp['status'] == 'success':
        token = resp['data']
        # 3. 注入 Token
        driver.execute_script(f'document.querySelector("[name=h-captcha-response]").value = "{token}";')
        driver.execute_script('hcaptcha.execute();')
        print("Token 注入成功")
    else:
        raise Exception(f"NopeCHA API 识别失败: {resp}")

def run_browser():
    chrome_options = Options()
    chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://eternalzero.cloud/login")
        # 登录、隐私清理逻辑... (同前)
        
        # 处理 hCaptcha
        if "h-captcha" in driver.page_source:
            solve_hcaptcha(driver)
            
        # 点击续费
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        driver.execute_script("arguments[0].click();", renew_btn)
        
        # ... 后续逻辑 ...
    finally:
        driver.quit()
