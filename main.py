from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from plyer import notification
import random
import time
import os

def is_captcha_present(driver):
    try:
        driver.find_element(By.XPATH, "//div[contains(@class, 'captcha') or contains(@id, 'captcha')]")
        return True
    except NoSuchElementException:
        return False

def send_captcha_alert():
    notification.notify(
        title="CAPTCHA Detected!",
        message="TikTok CAPTCHA detected. Manual action required.",
        timeout=10
    )

def is_browser_alive(driver):
    try:
        # A harmless JS command that will fail if the browser is closed
        driver.execute_script("return 1 + 1")
        return True
    except WebDriverException:
        return False

driver_path = os.path.join(os.getcwd(), "chromedriver.exe")
service = Service(driver_path)

project_path = os.path.dirname(os.path.abspath(__file__))
profile_path = os.path.join(project_path, "SeleniumProfile")

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(f"--user-data-dir={profile_path}")
options.add_argument(r"--profile-directory=Default")

driver = webdriver.Chrome(service=service, options=options)

driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
    Object.defineProperty(navigator, 'webdriver', {
      get: () => undefined
    })
    """
})

with open('urls.txt', "r") as url_file:
    urls = url_file.readlines()

for url in urls:
    try:
        driver.get(url.strip())
        time.sleep(2)
        driver.execute_script("document.querySelector('video').pause()")

        # Check CAPTCHA immediately
        if is_captcha_present(driver):
            send_captcha_alert()
            print("CAPTCHA detected. Waiting for manual resolution...")
            while is_captcha_present(driver):
                time.sleep(5)
            print("CAPTCHA solved. Continuing...")

        # Try to open the comment section
        while True:
            try:
                if not is_browser_alive(driver):
                    print("Browser appears to be closed. Exiting.")
                    driver.quit()
                    exit()
                comment_button = driver.find_element(By.XPATH, '//*[@id="main-content-video_detail"]/div/div[2]/div[1]/div[1]/div[1]/div[4]/div[2]/button[2]/span')
                comment_button.click()
                break
            except WebDriverException:
                print("Browser was closed. Exiting.")
                driver.quit()
                exit()
            except Exception as e:
                print("Couldn't find comment button:", e)
                time.sleep(2)

        # Try to like comments
        try:
            time.sleep(2)
            id = 1
            max_retries = 3
            retry_count = 0

            while True:
                if not is_browser_alive(driver):
                    print("Browser appears to be closed. Exiting.")
                    driver.quit()
                    exit()

                try:
                    tempXPATH = f'//*[@id="main-content-video_detail"]/div/div[2]/div[1]/div[2]/div[2]/div[{id}]/div[1]/div[2]/div[2]/div/div/span'
                    iframe = driver.find_element(By.XPATH, tempXPATH)
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", iframe)
                    time.sleep(random.uniform(0.25, 0.75))

                    like_button = driver.find_element(By.XPATH, tempXPATH)
                    time.sleep(random.uniform(0.25, 0.75))
                    like_button.click()
                    id += 1
                    retry_count = 0  # reset retry count after success

                except NoSuchElementException:
                    print("No more comment like buttons found.")
                    break

                except WebDriverException as e:
                    print("WebDriver error:", e)
                    if is_captcha_present(driver):
                        send_captcha_alert()
                        print("CAPTCHA detected. Waiting for manual resolution...")
                        while is_captcha_present(driver):
                            time.sleep(5)
                        print("CAPTCHA solved. Continuing...")
                    else:
                        retry_count += 1
                        if retry_count >= max_retries:
                            print("Too many errors. Stopping.")
                            break
                        print(f"Retrying ({retry_count}/{max_retries})...")
                        time.sleep(2)
        except Exception as e:
            print("Couldn't find like button:", e)

    except WebDriverException:
        print("Browser was closed unexpectedly. Ending session.")
        driver.quit()
        exit()

time.sleep(10)
print("Finished clicking buttons.")
driver.quit()