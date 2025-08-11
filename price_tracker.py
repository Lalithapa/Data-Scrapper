import os
import time
import pandas as pd
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium_stealth import stealth

# --- Load Proxy Credentials ---
load_dotenv(dotenv_path="AUTOMATION_PROXIES")

PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")

# Build proxy string if provided
proxy_option = None
if PROXY_HOST and PROXY_PORT:
    if PROXY_USERNAME and PROXY_PASSWORD:
        proxy_option = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    else:
        proxy_option = f"http://{PROXY_HOST}:{PROXY_PORT}"


def get_driver():
    """Initialize undetected Chrome with stealth and proxy settings."""
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")

    # Run in headed mode in Actions to reduce bot detection
    # (GitHub Actions needs XVFB to display)
    chrome_options.add_argument("--headless=new")  # remove if you want visible browser in local

    if proxy_option:
        chrome_options.add_argument(f"--proxy-server={proxy_option}")

    driver = uc.Chrome(options=chrome_options)

    # Apply stealth tweaks
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
    )

    return driver


def fetch_price(url):
    driver = get_driver()
    driver.get(url)
    time.sleep(3)  # Let page load

    # Amazon specific fix — click "Continue shopping" if shown
    try:
        if "Continue shopping" in driver.page_source:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' or @value='Continue shopping'] | //button[contains(text(), 'Continue shopping')]"))
            )
            btn.click()
            time.sleep(2)
    except:
        pass

    price = None
    try:
        # Generic price detection — update with your selectors
        possible_selectors = [
            "//span[@id='priceblock_ourprice']",
            "//span[@id='priceblock_dealprice']",
            "//span[contains(@class,'a-price-whole')]",
            "//div[contains(@class,'pdp-price')]",  # Myntra / Tira style
            "//span[contains(text(),'₹')]"
        ]
        for selector in possible_selectors:
            try:
                el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                price = el.text.strip()
                if price:
                    break
            except:
                continue
    finally:
        driver.quit()

    return price


if __name__ == "__main__":
    input_file = "products_new.xlsx"
    df = pd.read_excel(input_file)

    prices = []
    for idx, row in df.iterrows():
        url = row.get("URL")
        if not url:
            prices.append(None)
            continue
        print(f"Fetching price for {url}...")
        prices.append(fetch_price(url))

    df["Fetched Price"] = prices
    df.to_excel("Scraped_Product_Prices.xlsx", index=False)
    print("✅ Price scraping completed and saved to Scraped_Product_Prices.xlsx")