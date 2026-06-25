import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

# ... (send_telegram 和 get_captcha_token 函数保持不变) ...

def get_captcha_token(sitekey, url):
    # (此部分逻辑保持不变)
    pass

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
        driver.get("https://eternalzero.cloud/servers/5541/info")
        
        # 1. 必须先处理广告
        clear_all_ads(driver)
        
        # 2. 改进：使用显式等待查找验证码容器，且考虑到 iframe 嵌套可能
        print("正在等待验证码加载...")
        # 尝试等待 h-captcha 类名出现，或者等待包含 h-captcha 的 iframe
        try:
            captcha_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".h-captcha, iframe[src*='hcaptcha']")))
            
            # 如果是 iframe，我们需要切入进去
            if captcha_el.tag_name == "iframe":
                driver.switch_to.frame(captcha_el)
                # 重新定位 iframe 内部的 sitekey 或者在外部寻找
                driver.switch_to.default_content()
            
            sitekey = driver.execute_script("return document.querySelector('.h-captcha').getAttribute('data-sitekey')")
        except Exception as e:
            print(f"未能自动定位验证码: {e}")
            # 调试：打印页面源码的前一部分，方便后续排查
            print(driver.page_source[:500])
            raise

        print(f"获取到 Sitekey: {sitekey}")
        token = get_captcha_token(sitekey, driver.current_url)
        
        if token:
            driver.execute_script(f'document.querySelector("[name=h-captcha-response]").value = "{token}";')
            driver.execute_script("hcaptcha.execute();") 
            print("验证码已提交。")
        
        # 3. 点击续费
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        renew_btn.click()
        
        time.sleep(5)
        driver.save_screenshot("result.png")
        print("操作完成。")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser()
