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
import time
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)
app.secret_key = "ikea_stock_checker_secret_key"

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
    # Return empty dict with default values
    return {"searches": [], "location": ""}


# Function to save searches to JSON file
def save_searches(data):
    with open(SEARCHES_FILE, 'w') as file:
        json.dump(data, file)


# Main function to check IKEA product availability
def check_product_availability(location, search_query):
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
    # options.add_argument("--headless")

    try:
        # Start browser and navigate to IKEA website
        browser = webdriver.Chrome(options=options)
        browser.get('https://www.ikea.com/ca/en/')

        # Try to load saved cookies to speed up access and avoid captchas
        cookies_loaded = load_cookies(browser, COOKIES_FILE)
        if not cookies_loaded:
            print("No saved cookies found. Will create new ones after this session.")

            # Select store location first
            try:
                print("Selecting store location...")
                # Wait for store picker button to appear
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '#hnf-header-storepicker > a')))

                # Click on store picker button
                select_store_button = browser.find_element(
                    By.CSS_SELECTOR, '#hnf-header-storepicker > a')
                select_store_button.click()

                # Wait for store search box to appear
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '#hnf-store-search')))

                # Find and fill the store search box
                location_search_box = browser.find_element(
                    By.CSS_SELECTOR, '#hnf-store-search')

                print(f"Entering location: {location}")
                location_search_box.clear()
                location_search_box.send_keys(
                    location)  # Simulate the user typing
                # Simulate the user pressing enter
                location_search_box.send_keys(Keys.RETURN)

                # Wait until at least one store button appears
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[starts-with(@id, 'choice-')]/button"))
                )

                # Wait until it's clickable
                store_buttons = WebDriverWait(browser, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[starts-with(@id, 'choice-')]/button"))
                )

                # Try clicking the first store button
                try:
                    first_store = store_buttons[0]
                    WebDriverWait(browser, 10).until(EC.element_to_be_clickable(
                        (By.XPATH, "//div[starts-with(@id, 'choice-')]/button")))
                    browser.execute_script(
                        "arguments[0].scrollIntoView();", first_store)
                    time.sleep(1)  # Short wait for scroll
                    first_store.click()
                    print("Store selected successfully.")
                except Exception as e:
                    print(f"Failed to click store button: {e}")

                # Wait for the page to update with the selected store
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '#ikea-search-input')))

            except Exception as e:
                print(f"Error selecting store: {e}")
                return None

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


# Main page (URL to function)
@app.route('/')
def index():
    # Get all saved searches
    saved_data = load_saved_searches()

    # Show the index.html page
    # Send information:
    # 1. searches: the list of saved searches
    # 2. location: the saved location
    # 3. results: any results we have from checking products
    # 4. is_checking: If currently checking a product
    return render_template('index.html',
                           searches=saved_data["searches"],
                           location=saved_data["location"],
                           results=search_results,
                           is_checking=is_checking)


# Will be called periodically to see if page should be refreshed
@app.route('/check_status')
def check_status():
    return jsonify({
        "is_checking": is_checking
    })


# When search form is submitted
# Only responds to form submissions
@app.route('/search', methods=['POST'])
def search():
    # .strip() -- remove any spaces at the beginning or end
    query = request.form.get('query', '').strip()
    location = request.form.get('location', '').strip()

    # If they didn't type anything, show an error message
    if not query:
        # redirect - back to main page
        return redirect(url_for('index'))

    saved_data = load_saved_searches()

    # If item is not in the list, add it
    if query not in saved_data["searches"]:
        saved_data["searches"].append(query)  # Add to the list

    # Update the saved location
    saved_data["location"] = location

    save_searches(saved_data)

    # Start checking IKEA's website in the background
    # "thread" - separate mini-program that runs alongside the main program so website does not freeze
    threading.Thread(target=check_product_availability,
                     args=(location, query,)).start()

    # Show a message to let the user know we're checking
    flash(f"Checking availability for: {query}")
    # Send the user back to the main page
    return redirect(url_for('index'))


# DELETE
# <query> in URL is a placeholder (for actual search text)
@app.route('/delete/<query>')
def delete_search(query):
    saved_data = load_saved_searches()

    # If the search is in our list, remove it
    if query in saved_data["searches"]:
        saved_data["searches"].remove(query)
        save_searches(saved_data)

        # Remove any results we have for the item
        if query in search_results:
            del search_results[query]

    # Redirect to main page
    return redirect(url_for('index'))


# CHECK ALL
@app.route('/check_all')
def check_all():
    saved_data = load_saved_searches()
    location = saved_data["location"]

    # If already checking, don't start another check
    if is_checking:
        return redirect(url_for('index'))

    # Check each saved search one by one
    def check_all_products():
        for query in saved_data["searches"]:
            check_product_availability(location, query)

    # Start checking all products in the background using a thread
    threading.Thread(target=check_all_products).start()

    # Redirect to main page
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
