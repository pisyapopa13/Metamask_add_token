from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.expected_conditions import invisibility_of_element_located
import time
import random
import threading
from queue import Queue
from selenium.common.exceptions import NoSuchElementException

max_simultaneous_profiles = 3
metamask_url = f"chrome-extension://cfkgdnlcieooajdnoehjhgbmpbiacopjflbjpnkm/home.html#"
chrome_driver_path = Service("C:\\you\\personal\\path\\to\\chromedriver-win-x64.exe")

start_idx = int(input("Enter the starting index of the profile range: "))
end_idx = int(input("Enter the ending index of the profile range: "))


networks = [
    ("//*[contains(text(), 'Optimism')]", "Optimism", "0x7f5c764cbc14f9669b88837ca1490cca17c31607"),
    ("//*[contains(text(), 'Arbitrum One')]", "Arbitrum", "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8"),
    ("//*[contains(text(), 'Avalanche Network C-Chain')]", "Avalanche", "0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e"),
    ("//*[contains(text(), 'Polygon Mainnet')]", "Polygon", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"),
    ("//*[contains(text(), 'Fantom Opera')]", "Fantom", "0x04068da6c83afcfa0e13ba15a6696662335d5b75"),
    ("//*[contains(text(), 'BNB Smart Chain (previously Binance Smart Chain Mainnet)')]", "BNB", "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"),
]

with open("config\\profile_ids.txt", "r") as file:
    profile_ids = [line.strip() for line in file.readlines()]
with open("config\\passwords.txt", "r") as file:
    passwords = [line.strip() for line in file.readlines()]
def input_text_if_exists(driver, locator, text, by=By.XPATH, timeout=20):
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, locator))
            )
            element.send_keys(text)
            return True
        except TimeoutException:
            return False
        except StaleElementReferenceException:
            attempts += 1
            time.sleep(3)
    return False
def click_if_exists(driver, locator, by=By.XPATH):
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((by, locator))
            )
            WebDriverWait(driver, 10).until(
                invisibility_of_element_located((By.CSS_SELECTOR, ".loading-overlay"))
            )

            element.click()
            return True
        except TimeoutException:
            return False
        except StaleElementReferenceException:
            attempts += 1
            time.sleep(3)
    return False
def wait_until_input_filled(driver, locator, timeout=30, by=By.XPATH):
    WebDriverWait(driver, timeout).until(
        lambda d: d.find_element(by, locator).get_attribute("value") != ""
    )
def worker():
    while True:
        idx, profile_id = task_queue.get()
        if profile_id is None:
            break
        password = passwords[idx - 1]
        process_profile(idx, profile_id, password)
        task_queue.task_done()
def wait_for_invisibility(driver, xpath, timeout=10):

    WebDriverWait(driver, timeout).until(
        EC.invisibility_of_element_located((By.XPATH, xpath)))
def element_exists(driver, xpath):
    time.sleep(random.uniform(1.2, 1.7))
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        return True
    except NoSuchElementException:
        return False
def process_profile(idx, profile_id, password):

    print(f"Opening ID {idx}: {profile_id}")
    req_url = f'http://localhost:3001/v1.0/browser_profiles/{profile_id}/start?automation=1'
    response = requests.get(req_url)
    response_json = response.json()
    print(response_json)
    port = str(response_json['automation']['port'])
    options = webdriver.ChromeOptions()
    options.debugger_address = f'127.0.0.1:{port}'
    driver = webdriver.Chrome(service=chrome_driver_path, options=options)
    initial_window_handle = driver.current_window_handle

    driver.get(metamask_url)
    try:
        for tab in driver.window_handles:
            if tab != initial_window_handle:
                driver.switch_to.window(tab)
                driver.close()
        driver.switch_to.window(initial_window_handle)
        password_input = '//*[@id="password"]'
        input_text_if_exists(driver, password_input, passwords[idx - 1])
        click_if_exists(driver, '//*[@id="app-content"]/div/div[3]/div/div/button')
        click_if_exists(driver, '/html/body/div[2]/div/div/section/div[1]/div/button')

        for network_xpath, network_name, contract_address in networks:
            click_if_exists(driver, "/html/body/div[1]/div/div[1]/div/div[2]/div/div/span")
            click_if_exists(driver, network_xpath)
            click_if_exists(driver, '/html/body/div[2]/div/div/section/div[3]/button')
            click_if_exists(driver, "/html/body/div[1]/div/div[3]/div/div/div/div[3]/div[2]/div[3]/div[2]/a")
            contract_input_xpath = "/html/body/div[1]/div/div[3]/div/div[2]/div[1]/div/div[2]/div/input"
            contract_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, contract_input_xpath)))
            contract_input.send_keys(contract_address)
            time.sleep(random.uniform(3.5, 3.7))
            click_if_exists(driver, "/html/body/div[1]/div/div[3]/div/div[2]/div[2]/footer/button")
            click_if_exists(driver, "/html/body/div[1]/div/div[3]/div/div[3]/footer/button[2]")
        time.sleep(random.uniform(3.5, 5))
        print(f"Done for profile № {idx}")
        driver.close()
    except Exception as e:
        print(f"failed for profile № {idx}! {e} ")
        driver.quit()


task_queue = Queue(max_simultaneous_profiles)
threads = []

for _ in range(max_simultaneous_profiles):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

for idx, profile_id in zip(range(start_idx, end_idx + 1), profile_ids[start_idx - 1:end_idx]):
    task_queue.put((idx, profile_id))
    time.sleep(5)

task_queue.join()

for _ in range(max_simultaneous_profiles):
    task_queue.put((None, None))

for t in threads:
    t.join()