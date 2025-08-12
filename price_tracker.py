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
# INPUT_PATH = "/content/drive/MyDrive/ScraperProject/products_new.xlsx"
# OUTPUT_PATH = f"/content/drive/MyDrive/ScraperProject/Scraped_Product_Prices_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
INPUT_PATH = "products_new.xlsx"
OUTPUT_PATH = f"Scraped_Product_Prices_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
HEADLESS = True

# Load env (created by workflow step)
load_dotenv(dotenv_path="AUTOMATION_PROXIES")

# --- PROXY CONFIG (for requests, not Selenium) ---
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")

logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

print("[proxy] using proxies:",
      bool(PROXY_USERNAME and PROXY_PASSWORD and PROXY_HOST and PROXY_PORT))

# ---------- DEBUG HELPERS ----------
DEBUG_DIR = "debug"
os.makedirs(DEBUG_DIR, exist_ok=True)

def save_debug(driver, name):
    """Save a screenshot and the current HTML for post-run inspection."""
    try:
        driver.save_screenshot(os.path.join(DEBUG_DIR, f"{name}.png"))
        with open(os.path.join(DEBUG_DIR, f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"[debug] saved {name}.png and {name}.html")
    except Exception as e:
        print(f"[debug] save failed for {name}: {e}")

def try_accept_common_banners(driver):
    """Best-effort accept cookies/consent so price elements can render."""
    # Add more site-specific locators as you discover them in debug HTML
    candidates = [
        (By.ID, "sp-cc-accept"),  # Amazon EU cookie banner
        (By.XPATH, "//button[contains(., 'Accept All')]"),
        (By.XPATH, "//button[contains(., 'Accept all')]"),
        (By.XPATH, "//button[contains(., 'Accept')]"),
        (By.XPATH, "//button[contains(., 'I agree')]"),
        (By.CSS_SELECTOR, "button[aria-label='Accept']"),
    ]
    for by, sel in candidates:
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            time.sleep(0.3)
            break
        except Exception:
            pass

def gentle_scroll(driver):
    """Nudge the page to trigger lazy content in headless."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(0.7)
    except Exception:
        pass

# ---------- SELENIUM DRIVER ----------
def init_driver():
    options = Options()

    # Classic headless is often more predictable on CI than --headless=new
    if HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=en-US")
    options.add_argument("user-agent=Mozilla/5.0")

    # DO NOT route Selenium via auth proxy in CI (often breaks). Keep it simple.
    # If you have an IP-allowlisted proxy (no auth), you could enable:
    # options.add_argument(f"--proxy-server=http://{PROXY_HOST}:{PROXY_PORT}")

    # Point to Chrome binary installed in GitHub Actions
    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(45)
    driver.implicitly_wait(2)

    # ------ ADD THESE CDP OVERRIDES AFTER DRIVER IS CREATED ------
    try:
        # Pretend we're in India + English
        driver.execute_cdp_cmd("Emulation.setLocaleOverride", {"locale": "en-IN"})
        driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "Asia/Kolkata"})
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/114.0.0.0 Safari/537.36"),
            "acceptLanguage": "en-IN,en;q=0.9"
        })
    except Exception as e:
        print("[debug] CDP override failed:", e)
    # -------------------------------------------------------------

    return driver

# ---------- REQUESTS HELPER (uses your proxy) ----------
def fetch_page(url):
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/114.0.0.0 Safari/537.36"),
        "Accept-Language": "en-US,en;q=0.9"
    }

    proxies = None
    if PROXY_USERNAME and PROXY_PASSWORD and PROXY_HOST and PROXY_PORT:
        proxies = {
            "http": f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}",
            "https": f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}",
        }

    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=20)
        if response.status_code == 200:
            return response.text
        logging.warning(f"Requests non-200 for {url}: {response.status_code}")
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
        try_accept_common_banners(driver)
        gentle_scroll(driver)
        if "Continue shopping" in driver.page_source:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' or @value='Continue shopping'] | //button[contains(text(), 'Continue shopping')]"))
            )
            btn.click()
            time.sleep(2)

        wait = WebDriverWait(driver, 20)
        selectors = [
            (By.CSS_SELECTOR, "#centerCol .a-price-whole"),
            (By.ID, "priceblock_ourprice"),   # legacy
            (By.ID, "priceblock_dealprice"),  # legacy
        ]

        for by, sel in selectors:
            try:
                el = wait.until(EC.presence_of_element_located((by, sel)))
                txt = el.text.strip()
                if txt:
                    save_debug(driver, "amazon_success")
                    return txt.replace('₹', '').replace(',', '').strip()
            except Exception:
                continue

        save_debug(driver, "amazon_no_price")
    except Exception as e:
        logging.error(f"Amazon error: {url} — {e}")
        save_debug(driver, "amazon_error")
    finally:
        driver.quit()
    return None

def get_price_tira_selenium(url):
    driver = init_driver()
    try:
        driver.get(url)
        try_accept_common_banners(driver)
        gentle_scroll(driver)

        wait = WebDriverWait(driver, 20)
        selectors = [
            (By.CSS_SELECTOR, "span.current-amount"),
            (By.CSS_SELECTOR, ".product-cost-container #item_price"),
            (By.CSS_SELECTOR, "#item_price"),
        ]
        for by, sel in selectors:
            try:
                el = wait.until(EC.presence_of_element_located((by, sel)))
                txt = el.text.strip()
                if txt:
                    save_debug(driver, "tira_success")
                    return txt.replace('₹', '').replace(',', '').strip()
            except Exception:
                continue
        save_debug(driver, "tira_no_price")
    except Exception as e:
        logging.error(f"Tira error: {url} — {e}")
        save_debug(driver, "tira_error")
    finally:
        driver.quit()
    return None

def get_price_myntra_selenium(url):
    driver = init_driver()
    try:
        driver.get(url)
        try_accept_common_banners(driver)
        gentle_scroll(driver)

        wait = WebDriverWait(driver, 20)
        selectors = [
            (By.CSS_SELECTOR, "span.pdp-price strong"),
            (By.CSS_SELECTOR, ".pdp-discount-container span.pdp-price strong"),  # old
        ]
        for by, sel in selectors:
            try:
                el = wait.until(EC.presence_of_element_located((by, sel)))
                txt = el.text.strip()
                if txt:
                    save_debug(driver, "myntra_success")
                    return txt.replace('₹', '').replace(',', '').strip()
            except Exception:
                continue
        save_debug(driver, "myntra_no_price")
    except Exception as e:
        logging.error(f"Myntra error: {url} — {e}")
        save_debug(driver, "myntra_error")
    finally:
        driver.quit()
    return None

def get_price_blinkit_data_selenium(url):
    html = fetch_page(url)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.select_one(".categories-table")
        # Implement proper selector if Blinkit shows data without login/geo gate
    return None

# ---------- STORE FUNCTION MAP ----------
STORE_FUNCTIONS = {
    'Nykaa Link': get_price_nykaa,            # requests
    'Amazon Link': get_price_amazon_selenium, # selenium
    'Myntra': get_price_myntra_selenium,      # selenium
    'Tira': get_price_tira_selenium,          # selenium
}

# ---------- MAIN RUNNER ----------
def main():
    df = pd.read_excel(INPUT_PATH)
    output_df = df.copy()
    # print("Columns: test to check number of list", list(df.columns))
    for idx, row in output_df.iterrows():
        sku = row.get("Sku Code", f"Row {idx+1}")
        print(f"\n🔍 {sku}")
        for col, scraper_func in STORE_FUNCTIONS.items():
            url = row.get(col)
            if isinstance(url, str) and url.startswith("http"):
                print(f"  ⏳ {col} → ", end="")
                try:
                    # price = 200
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