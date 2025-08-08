import logging
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------- CONFIG ----------
INPUT_PATH = "products_new.xlsx"
# OUTPUT_PATH = "Scraped_Product_Prices.xlsx"
OUTPUT_PATH = f"Scraped_Product_Prices_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

# INPUT_PATH = "/content/drive/My Drive/ScraperProject/products.xlsx"
# OUTPUT_PATH = "/content/drive/My Drive/ScraperProject/Scraped_Product_Prices.xlsx"

HEADLESS = True

# load_dotenv()
load_dotenv(dotenv_path="AUTOMATION_PROXIES")

# --- PROXY CONFIG ---
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")

logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------- SELENIUM DRIVER ----------
def init_driver():
    # options = Options()
    # if HEADLESS:
    #     options.add_argument("--headless")
    #     options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920,1080")
    # options.add_argument("user-agent=Mozilla/5.0")
    # options.add_argument("--disable-blink-features=AutomationControlled")
    # service = ChromeService(ChromeDriverManager().install())
    # return webdriver.Chrome(service=service, options=options)

    # Updating the driver initialization to use the latest Chrome options and ensure compatibility with CI environments.
    options = Options()
    if HEADLESS:
     options.add_argument("--headless")     # <-- classic headless
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=en-US")
    options.add_argument("user-agent=Mozilla/5.0")

    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(45)
    driver.implicitly_wait(2)
    return driver

DEBUG_DIR = "debug"
os.makedirs(DEBUG_DIR, exist_ok=True)

def save_debug(driver, name):
    """Save screenshot and HTML of the current page for debugging"""
    try:
        driver.save_screenshot(f"{DEBUG_DIR}/{name}.png")
        with open(f"{DEBUG_DIR}/{name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except Exception as e:
        print("[debug] save failed:", e)

# ---------- REQUESTS HELPER ----------
def fetch_page(url):
    # headers = {"User-Agent": "Mozilla/5.0"}
    # try:
    #     response = requests.get(url, headers=headers, timeout=10)
    #     if response.status_code == 200:
    #         return response.text
    # except Exception as e:
    #     logging.warning(f"Requests failed: {url} — {e}")
    # return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    proxies = {
        "http": f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}",
        "https": f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}",
    }

    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logging.warning(f"Requests failed: {url} — {e}")
    return None

# ---------- INDIVIDUAL SCRAPER FUNCTIONS ----------
def get_price_nykaa(url):
    html = fetch_page(url)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.select_one(".css-14y2xde span.css-1jczs19")
        if tag:
            return tag.text.replace('₹', '').replace(',', '').strip()
    return None

def get_price_amazon_selenium(url):
    driver = init_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        for sel in [
            (By.CSS_SELECTOR, "#apex_desktop .a-price .a-offscreen"),
            (By.CSS_SELECTOR, "#corePrice_feature_div .a-offscreen"),
            (By.CSS_SELECTOR, ".a-price .a-offscreen"),
            (By.ID, "priceblock_ourprice"),
            (By.ID, "priceblock_dealprice"),
        ]:
            try:
                price = wait.until(EC.presence_of_element_located(sel)).text
                save_debug(driver, "amazon_success")  # 📌 Save debug
                return price.replace('₹', '').replace(',', '').strip()
            except:
                continue
    except Exception as e:
        logging.error(f"Amazon error: {url} — {e}")
        save_debug(driver, "amazon_error")  # 📌 Save debug
    finally:
        driver.quit()
    return None

def get_price_tira_selenium(url):
    driver = init_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-cost-container #item_price")))
        save_debug(driver, "tire_success")  # 📌 Save debug
        return el.text.replace('₹', '').replace(',', '').strip()
    except Exception as e:
        logging.error(f"Tira error: {url} — {e}")
        save_debug(driver, "tira_error")  # 📌 Save debug

    finally:
        driver.quit()
    return None

def get_price_myntra_selenium(url):
    driver = init_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".pdp-discount-container span.pdp-price strong")))
        save_debug(driver, "myntra_success")  # 📌 Save debug
        return el.text.replace('₹', '').replace(',', '').strip()
    except Exception as e:
        logging.error(f"Myntra error: {url} — {e}")
        save_debug(driver, "myntra_error")  # 📌 Save debug

    finally:
        driver.quit()
    return None

def get_price_blinkit_selenium(url):
    driver = init_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".tw-flex.tw-items-center.tw-gap-1 .tw-text-400.tw-font-bold")))
        return el.text.replace('₹', '').replace(',', '').strip()
    except Exception as e:
        logging.error(f"Blinkit error: {url} — {e}")
    finally:
        driver.quit()
    return None
def get_price_blinkit_data_selenium(url):
    html = fetch_page(url)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.select_one(".categories-table")
        # if tag:
        #     return tag.text.replace('₹', '').replace(',', '').strip()
    return None

# ---------- STORE FUNCTION MAP ----------
STORE_FUNCTIONS = {
    'Nykaa Link': get_price_nykaa,
    'Amazon Link': get_price_amazon_selenium,
    'Myntra': get_price_myntra_selenium,
    'Tira': get_price_tira_selenium,
    # 'Blinkit': get_price_blinkit_selenium,
}

# ---------- MAIN RUNNER ----------
def main():
    df = pd.read_excel(INPUT_PATH)
    output_df = df.copy()
    
    # idx = 0  # Only run for the first row
    # row = output_df.iloc[idx]

    for idx, row in output_df.iterrows():
        sku = row.get("Sku Code", f"Row {idx+1}")
        print(f"\n🔍 {sku}")
        for col, scraper_func in STORE_FUNCTIONS.items():
            url = row.get(col)
            # print(f" This  {url}")
            if isinstance(url, str) and url.startswith("http"):
                print(f"  ⏳ {col} → ", end="")
                try:
                    price = scraper_func(url)
                    if price:
                        print(f"₹{price}")
                        output_df.at[idx, col] = price
                    else:
                        print("N/A")
                        output_df.at[idx, col] = "N/A"
                except Exception as e:
                    print("Error")
                    logging.error(f"{col} failed for {url} — {e}")
                    output_df.at[idx, col] = "Error"
                time.sleep(random.uniform(1, 2))

    output_df.to_excel(OUTPUT_PATH, index=False)
    print(f"\n✅ Scraping complete! Results saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()