from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import os


def save_cookies(browser, path):
    with open(path, 'wb') as file:
        pickle.dump(browser.get_cookies(), file)
    print(f"Cookies saved to {path}")


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


def main():
    print("What product would you like to search for on IKEA?")
    search_query = input()

    options = webdriver.ChromeOptions()
    browser = webdriver.Chrome(options=options)
    browser.get('https://www.ikea.com/ca/en/')

    cookies_loaded = load_cookies(browser, 'ikea_cookies.pkl')
    if not cookies_loaded:
        print("No saved cookies found. Will create new ones after this session.")

    WebDriverWait(browser, 10).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '#ikea-search-input')))
    search_box = browser.find_element(By.CSS_SELECTOR, '#ikea-search-input')

    print(f"Entering search query: {search_query}")
    search_box.clear()
    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)

    print("Waiting for search results...")
    WebDriverWait(browser, 10).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a[href*='/ca/en/p/']"))
    )

    product_url = None
    products = browser.find_elements(By.CSS_SELECTOR, "a[href*='/ca/en/p/']")
    if products:
        product_url = products[0].get_attribute('href')
        print(f"Product URL: {product_url}")
    else:
        print("No products found. Saving screenshot.")
        browser.save_screenshot("search_results.png")
        return

    print(f"Navigating to product page: {product_url}")
    browser.get(product_url)

    print("Waiting for product page to load...")
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Looking for check stock button...")

    check_stock_button = None

    try:
        buttons = browser.find_elements(
            By.CSS_SELECTOR, "#pip-buy-module-content > div.pip-section-group.pip-availability-group.js-availability-group.js-availability-group-dynamic > div.pip-section-group__content > button > div.pip-section__content--wrapper")
        for button in buttons:
            if any(term in button.text.lower() for term in ["stock", "store", "availability"]):
                check_stock_button = button

    except Exception as e:
        print(f"Error looking for check stock button: {e}.")

    if not check_stock_button:
        print("No stock check button found. Exiting.")
        return

    check_stock_button.click()
    print("Clicked check stock button.")
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "span.pip-store-availability-section__availability-status-text span")
        )
    )

    try:
        status_element = browser.find_element(
            By.CSS_SELECTOR,
            "span.pip-store-availability-section__availability-status-text span"
        )
        status = status_element.text
        if "in stock" in status.lower():
            print(f"✅ Product is in stock: {status}")
        else:
            print(f"❌ Product is not in stock: {status}")
    except Exception as e:
        print("⚠️ Could not find status element.")
        browser.save_screenshot("no_status_element.png")

    save_cookies(browser, 'ikea_cookies.pkl')
    print("Press Enter to close the browser...")
    input()
    browser.quit()


if __name__ == "__main__":
    main()
