# IKEA Stock Checker

This project is a Flask-based web app that helps users check real-time stock availability for IKEA products in specific store locations. It combines a clean UI with backend web-crawling automation using Selenium.

## Features
- **Live Stock Search**: Query IKEA inventory by product name or article number  
- **Location-Aware Results**: Filter results by city or store location  
- **Saved Searches**: Quickly recheck frequently monitored items  
- **Auto-Refresh**: Background polling while checking product availability  
- **Direct Links**: Go straight to the IKEA product page from the results  

## Prerequisites
- Python 3.8+  
- Google Chrome & ChromeDriver  
- Flask  
- Selenium  

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ikea-stock-checker.git
   cd ikea-stock-checker
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   py main.py
   ```

4. Open your browser and go to:
   ```
   http://localhost:5000
   ```

## ⚙️ Notes
- Ensure ChromeDriver matches your version of Google Chrome  
- For best results, ensure IKEA item is properly spelled   

## 🛡️ Disclaimer
This tool is not affiliated with or endorsed by IKEA.

---
