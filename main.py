from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import time
import pickle
import os

# Function to save browser cookies to a file


def save_cookies(browser, path):
    with open(path, 'wb') as file:
        pickle.dump(browser.get_cookies(), file)
    print(f"Cookies saved to {path}")

# Function to load cookies into the browser to find the location


def load_cookies(browser, path):
    if os.path.exists(path):
        with open(path, 'rb') as file:
            cookies = pickle.load(file)
        for cookie in cookies:
            try:
                browser.add_cookie(cookie)
            except:
                pass
        print("Cookies loaded successfully")
        return True
    return False


# Ask user for product to search
print("What product would you like to search for on IKEA?")
search_query = input()


# Open the browser and go to IKEA homepage
browser = webdriver.Chrome()
browser.get('https://www.ikea.com/ca/en/')


# Check if we have saved cookies and load them
cookies_loaded = load_cookies(browser, 'ikea_cookies.pkl')
if not cookies_loaded:
    print("No saved cookies found. Will create new ones after this session.")


# Wait for the page to load fully
time.sleep(2)

try:
    # Look for the search box and enter the search query
    search_box = browser.find_element(By.CSS_SELECTOR, '#ikea-search-input')
    search_box.clear()
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)

    # Wait for search results to load
    print("Waiting for search results...")
    time.sleep(5)

    # Find the first product in the search results and click on it
    first_product = browser.find_element(
        By.CSS_SELECTOR, 'a[class*="product"][class*="link"]')
    first_product.click()

    # Wait for product page to load
    time.sleep(4)
    print("Product page loaded")

    # Click the check stock button
    check_stock_button = browser.find_element(
        By.CSS_SELECTOR, '#pip-buy-module-content > div.pip-section-group.pip-availability-group.js-availability-group.js-availability-group-dynamic > div.pip-section-group__content > button')
    check_stock_button.click()

    # Wait for the modal to appear
    time.sleep(2)

    # Find the availability status text
    status_element = browser.find_element(By.CSS_SELECTOR, '#range-modal-mount-node > div > div.pip-skapa-focus-lock > div > div.pip-sheets__content-wrapper > div > div > div.pip-store-availability-section > div.pip-store-availability-section__availability > div.pip-store-availability-section__store > div > span > span.pip-status__label > span > span.pip-store-availability-section__availability-status-text > span')
    status = status_element.text

    if "in stock" in status.lower():
        print(f"Product is in stock. Status: {status}")
    else:
        print(f"Product is not in stock. Status: {status}")


except Exception as e:
    print(f"Error: {e}")

# Save the cookies for future use
save_cookies(browser, 'ikea_cookies.pkl')

# Keep the browser open until user presses Enter
time.sleep(100)
browser.quit()
