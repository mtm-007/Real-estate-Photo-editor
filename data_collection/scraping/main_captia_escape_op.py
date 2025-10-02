#from selenium import webdriver
import undetected_chromedriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time


#options = Options()
options = webdriver.ChromeOptions()
#options.add_argument("--headless=new")   # run without a GUI
options.add_argument("--no-sandbox")     # needed inside containers
options.add_argument("--disable-dev-shm-usage")  # avoid limited /dev/shm space

# options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
# options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
# options.add_argument("--window-size=1920,1080")
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option('useAutomationExtension', False)



# service = Service(executable_path='chromedriver-linux64/chromedriver')
# #driver = webdriver.Chrome(service=service, options=options)
driver = webdriver.Chrome(options=options)


# Hide webdriver property
# driver.execute_cdp_cmd('Network.setUserAgentOverride', {
#     "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
# })
# driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")


driver.get("https://google.com")

# wait = WebDriverWait(driver, 10)
# input_element = wait.until(
#     EC.element_to_be_clickable((By.CLASS_NAME,"gLFyf"))
# )
# input_element.click()
# time.sleep(2)
# input_element.send_keys("what is the weather here")
# time.sleep(1.5)
# input_element.send_keys(Keys.RETURN)

#time.sleep(3)
time.sleep(0.5)
input_element = driver.find_element(By.CLASS_NAME, "gLFyf")
time.sleep(0.5)
input_element.send_keys("what is the weather here" + Keys.ENTER)
time.sleep(0.5)
print(f"Title: {driver.title}")
driver.save_screenshot("result.png")
print("screenshot saved")
driver.quit()
print("driver quit run")
