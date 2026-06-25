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
    submit_url = "https://api.nopecha.com/v1/solve"
    payload = {"key": NOPECHA_KEY, "type": "hcaptcha", "sitekey": sitekey, "url": url}
    resp = requests.post(submit_url, json=payload)
    if resp.status_code != 200: return None
    task_id = resp.json().get("data")
    
    result_url = f"https://api.nopecha.com/v1/status?key={NOPECHA_KEY}&id={task_id}"
    for _ in range(20):
        time.sleep(3)
        res = requests.get(result_url).json()
        if res.get("status") == "solved":
            return res.get("data")
    return None

def clear_all_ads(driver):
    print("清理页面广告中...")
    for _ in range(5):
        btns = driver.find_elements(By.CSS_SELECTOR, "button.fc-cta-consent")
        if btns and btns[0].is_displayed():
            driver.execute_script("arguments[0].click();", btns[0])
            time.sleep(2)
        
        ad_btns = driver.find_elements(By.CSS_SELECTOR, "button.fc-rewarded-ad-button")
        if ad_btns and ad_btns[0].is_displayed():
            driver.execute_script("arguments[0].click();", ad_btns[0])
            time.sleep(30)
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
    wait = WebDriverWait(driver, 20)

    try:
        # 1. 登录
        driver.get("https://eternalzero.cloud/login")
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[contains(., 'Sign in')]").click()
        time.sleep(5)

        # 2. 跳转到 Info 页面
        driver.get("https://eternalzero.cloud/servers/5541/info")
        print("已进入 Info 页面，准备处理广告...")
        
        # 3. 处理广告
        clear_all_ads(driver)
        
        # 4. 现在才查找人机验证
        print("等待人机验证出现...")
        captcha_el = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "h-captcha")))
        sitekey = captcha_el.get_attribute("data-sitekey")
        
        print(f"检测到人机验证，Sitekey: {sitekey}，正在解决...")
        token = get_captcha_token(sitekey, driver.current_url)
        
        if token:
            driver.execute_script(f'document.querySelector("[name=h-captcha-response]").value = "{token}";')
            driver.execute_script("hcaptcha.execute();") 
            print("验证码已注入并执行。")
        
        # 5. 等待验证通过后点击续费
        time.sleep(5)
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        renew_btn.click()
        
        time.sleep(5)
        driver.save_screenshot("result.png")
        print("操作完成。")
        
    except Exception as e:
        print(f"流程出错: {e}")
        driver.save_screenshot("error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
