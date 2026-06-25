import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 从环境变量获取敏感信息 (GitHub Repository Secrets)
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
NOPECHA_KEY = os.getenv("NOPECHA_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message, image_path=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    if image_path:
        url_img = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(image_path, 'rb') as f:
            requests.post(url_img, data={"chat_id": TELEGRAM_CHAT_ID}, files={"photo": f})

def solve_hcaptcha(driver):
    # 此处接入 NopeCHA API 逻辑
    # 示例：通过向 NopeCHA 提交当前页面信息自动获取 token 并执行
    pass

def run_automation():
    options = Options()
    # options.add_argument("--headless") # 根据需要开启无头模式
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    try:
        # 1. 登录
        driver.get("https://eternalzero.cloud/login")
        driver.find_element(By.ID, "email").send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        
        # 鲁棒性按钮定位：通过包含特定文本的按钮定位
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in')]")))
        login_btn.click()

        # 处理欧洲隐私弹窗 (如果出现)
        try:
            privacy_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]") # 根据实际情况调整
            privacy_btn.click()
        except:
            pass

        # 2. 检查登录状态
        driver.get("https://eternalzero.cloud/servers/list")
        if "5541" not in driver.page_source:
            raise Exception("登录失败或未找到服务器信息")

        # 3. Renew 操作
        driver.get("https://eternalzero.cloud/servers/5541/info")
        
        # 处理人机验证
        solve_hcaptcha(driver)
        
        # 点击 Renew
        renew_btn = wait.until(EC.element_to_be_clickable((By.ID, "renew-button")))
        renew_btn.click()
        
        driver.save_screenshot("success.png")
        send_telegram_msg("服务器续费成功！", "success.png")

    except Exception as e:
        driver.save_screenshot("error.png")
        send_telegram_msg(f"操作失败: {str(e)}", "error.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
