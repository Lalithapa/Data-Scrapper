import logging
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------- CONFIG ----------
INPUT_PATH = "products.xlsx"
OUTPUT_PATH = "Scraped_Product_Prices.xlsx"
HEADLESS = True

# --- PROXY CONFIG ---
PROXY_USERNAME = "hvxkcxys-rotate"
PROXY_PASSWORD = "smvx89775mmq"
PROXY_HOST = "p.webshare.io"
PROXY_PORT = 80

logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------- SELENIUM DRIVER ----------
def init_driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0")
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

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
            (By.ID, "priceblock_ourprice"),
            (By.ID, "priceblock_dealprice"),
            (By.CSS_SELECTOR, "#centerCol .a-price-whole")
        ]:
            try:
                price = wait.until(EC.presence_of_element_located(sel)).text
                return price.replace('₹', '').replace(',', '').strip()
            except:
                continue
    except Exception as e:
        logging.error(f"Amazon error: {url} — {e}")
    finally:
        driver.quit()
    return None

def get_price_tira_selenium(url):
    driver = init_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-cost-container #item_price")))
        return el.text.replace('₹', '').replace(',', '').strip()
    except Exception as e:
        logging.error(f"Tira error: {url} — {e}")
    finally:
        driver.quit()
    return None

def get_price_myntra_selenium(url):
    driver = init_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".pdp-discount-container span.pdp-price strong")))
        return el.text.replace('₹', '').replace(',', '').strip()
    except Exception as e:
        logging.error(f"Myntra error: {url} — {e}")
    finally:
        driver.quit()
    return None

def get_price_blinkit_selenium(url):
    driver = init_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.Price__value")))
        return el.text.replace('₹', '').replace(',', '').strip()
    except Exception as e:
        logging.error(f"Blinkit error: {url} — {e}")
    finally:
        driver.quit()
    return None

# ---------- STORE FUNCTION MAP ----------
STORE_FUNCTIONS = {
    'Nykaa Link': get_price_nykaa,
    'Amazon Link': get_price_amazon_selenium,
    # 'Myntra': get_price_myntra_selenium,
    # 'Tira': get_price_tira_selenium,
    # 'Blinkit': get_price_blinkit_selenium,
}

# ---------- MAIN RUNNER ----------
def main():
    df = pd.read_excel(INPUT_PATH)
    output_df = df.copy()

    for idx, row in output_df.iterrows():
        sku = row.get("Sku Code", f"Row {idx+1}")
        print(f"\n🔍 {sku}")
        for col, scraper_func in STORE_FUNCTIONS.items():
            url = row.get(col)
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