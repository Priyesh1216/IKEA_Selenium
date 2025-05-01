from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle  # For saving/loading cookies
import os
import json
import threading
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)

# File paths for saved data
SEARCHES_FILE = "saved_searches.json"  # Stores user's saved searches
COOKIES_FILE = "ikea_cookies.pkl"  # Stores browser cookies for faster access

# Global variables
search_results = {}  # Store search results
is_checking = False  # Flag to track if a search is in progress


# Function to save browser cookies to file
def save_cookies(browser, path):
    with open(path, 'wb') as file:
        pickle.dump(browser.get_cookies(), file)
    print(f"Cookies saved to {path}")


# Function to load cookies from file into browser
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
    return False  # Return False if cookie file doesn't exist


# Function to load saved searches from file
def load_saved_searches():
    if os.path.exists(SEARCHES_FILE):
        with open(SEARCHES_FILE, 'r') as file:
            return json.load(file)
    return []  # Return empty list if file doesn't exist


# Function to save searches to JSON file
def save_searches(searches):
    with open(SEARCHES_FILE, 'w') as file:
        json.dump(searches, file)


# Main function to check IKEA product availability
def check_product_availability(search_query):
    global search_results, is_checking

    is_checking = True  # Set flag to indicate search is in progress

    # Initialize result dictionary with default values
    result = {
        "query": search_query,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Checking...",
        "product_name": "",
        "product_url": "",
        "product_image": "",
        "price": "",
        "error": None
    }

    search_results[search_query] = result

    # Set up Chrome browser options
    options = webdriver.ChromeOptions()

    # Browser checks info with no visible window
    options.add_argument("--headless")

    try:
        # Start browser and navigate to IKEA website
        browser = webdriver.Chrome(options=options)
        browser.get('https://www.ikea.com/ca/en/')

        # Try to load saved cookies to speed up access and avoid captchas
        cookies_loaded = load_cookies(browser, COOKIES_FILE)
        if not cookies_loaded:
            print("No saved cookies found. Will create new ones after this session.")

        # Wait for search box to appear and enter search query
        WebDriverWait(browser, 10).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#ikea-search-input')))
        search_box = browser.find_element(
            By.CSS_SELECTOR, '#ikea-search-input')

        print(f"Entering search: {search_query}")
        search_box.clear()
        search_box.send_keys(search_query)  # Simulate the user typing
        search_box.send_keys(Keys.RETURN)  # Simulate the user pressing enter

        print("Waiting for search results...")
        # Wait for search results to load (looking for product links)
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a[href*='/ca/en/p/']"))
        )

        # Get products from the search results
        product_url = None
        products = browser.find_elements(
            By.CSS_SELECTOR, "a[href*='/ca/en/p/']")

        # If products are present
        if products:
            # Get first product from search results
            product_url = products[0].get_attribute('href')
            result["product_url"] = product_url
            print(f"Product URL: {product_url}")

        else:
            # No products found
            print("No products found. Saving screenshot.")
            # Update the result dictionary
            result["status"] = "No products found"
            result["error"] = "No products matched your search query"
            save_cookies(browser, COOKIES_FILE)  # Save cookies before quitting
            browser.quit()
            is_checking = False
            return

        # Navigate to product page
        print(f"Navigating to product page: {product_url}")
        browser.get(product_url)

        print("Waiting for product page to load...")
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Get product name
        try:
            product_name = browser.find_element(
                By.CSS_SELECTOR, "span.pip-header-section__title--big").text
            result["product_name"] = product_name
        except:
            result["product_name"] = "Unknown Product"

        # Get product image
        try:
            product_image = browser.find_element(
                By.CSS_SELECTOR, "img.pip-image").get_attribute("src")
            result["product_image"] = product_image
        except:
            result["product_image"] = "/static/placeholder.jpg"

        # Find and click the check stock button
        print("Looking for check stock button...")
        check_stock_button = None

        try:
            buttons = browser.find_elements(
                By.CSS_SELECTOR, "#pip-buy-module-content > div.pip-section-group.pip-availability-group.js-availability-group.js-availability-group-dynamic > div.pip-section-group__content > button > div.pip-section__content--wrapper")
            for button in buttons:
                if any(term in button.text.lower() for term in ["stock", "store", "availability"]):
                    check_stock_button = button
                    break

        except Exception as e:
            print(f"Error looking for check stock button: {e}.")
            result["error"] = f"Error finding stock button: {str(e)}"

        # If no stock button found, exit
        if not check_stock_button:
            print("No stock check button found. Exiting.")
            result["status"] = "Could not check stock"
            result["error"] = "Stock check button not found"
            save_cookies(browser, COOKIES_FILE)
            browser.quit()
            is_checking = False
            return

        # Click the stock check button and wait for results
        check_stock_button.click()
        print("Clicked check stock button.")
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span.pip-store-availability-section__availability-status-text span")
            )
        )

        # Get stock status
        try:
            status_element = browser.find_element(
                By.CSS_SELECTOR,
                "span.pip-store-availability-section__availability-status-text span"
            )
            status = status_element.text
            if "in stock" in status.lower():
                result["status"] = f"✅ In Stock: {status}"
                print(f"✅ Product is in stock: {status}")
            else:
                result["status"] = f"❌ Not in Stock: {status}"
                print(f"❌ Product is not in stock: {status}")

        except Exception as e:
            print("⚠️ Could not find status element.")

            result["status"] = "⚠️ Status Unknown"
            result["error"] = "Could not find status element"

        # Save cookies and close browser
        save_cookies(browser, COOKIES_FILE)
        browser.quit()

    except Exception as e:
        # Handle any unexpected errors
        print(f"Error during search: {e}")
        result["status"] = "Error"
        result["error"] = str(e)
        try:
            browser.quit()
        except:
            pass  # Browser already quit

    is_checking = False  # Reset flag when search is complete


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
