# 🛒 Price Tracker Scraper

A Python-based project that scrapes **product prices** from major Indian beauty e-commerce websites like **Nykaa, Amazon, Myntra, Tira**, and **Blinkit** using **Selenium**, **BeautifulSoup**, and **rotating residential proxies**.

---

## 📁 Folder Structure

```
Data-Scrapper/
│
├── products.xlsx                # Input Excel file with product details and URLs
├── price_tracker.py            # Main Python script to execute the scraper
├── Scraped_Product_Prices.xlsx # Output Excel with extracted prices
├── scraper.log                 # Log file for warnings and errors
├── requirements.txt            # Python dependencies list
└── README.md                   # Documentation (this file)
```

---

## 🚀 What It Does

- ✅ Scrapes latest product prices from:
  - Nykaa (via requests + BeautifulSoup)
  - Amazon (via Selenium)
  - Myntra, Tira, Blinkit (via Selenium)
- ✅ Works with rotating **residential proxies** to avoid IP blocking
- ✅ Supports **headless mode** for background execution
- ✅ Saves all results to Excel file
- ✅ Logs all scraping events and failures to `scraper.log`
- ✅ Stores raw HTML files on failure for easier debugging

---

## ⚙️ Setup Instructions

### 🔧 1. Clone the repository
```bash
git clone https://github.com/yourusername/data-scrapper.git
cd data-scrapper
```

### 🐍 2. Set up a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # On Windows
# source venv/bin/activate   # On Mac/Linux
```

### 📦 3. Install all dependencies
```bash
pip install -r requirements.txt
```
If `distutils` error appears:
```bash
python -m ensurepip --upgrade
pip install setuptools
```

---

## 🧠 How It Works (Step-by-step)

### 🧩 Main Components:

1. **`products.xlsx`**
   - Input file containing columns: `Sku Code`, `Product Name`, and links for each store

2. **`price_tracker.py`**
   - Reads the Excel file using Pandas
   - For each URL, determines the store and calls the appropriate scraper function
   - Scraper uses either:
     - `requests` (for Nykaa)
     - `selenium` (for Amazon, Myntra, Tira, Blinkit)
   - Extracts price and saves to new Excel file

3. **Proxies Setup**
   - Selenium uses your proxy with this format:
     ```python
     options.add_argument('--proxy-server=http://USERNAME:PASSWORD@HOST:PORT')
     ```
   - Works best with **residential proxies** that support HTTPS and headless Chrome

4. **Headless Chrome**
   - Runs invisibly (without opening browser window)
   - Can be toggled with `HEADLESS = True`

5. **Error Logging**
   - All scraping issues go to `scraper.log`
   - HTML source is saved on failure to `debug_html/` folder

---

## ✅ Running the Scraper

### 1. Edit `products.xlsx`
Update the spreadsheet with product SKUs and URLs under each store's column:

| Sku Code | Nykaa Link | Amazon Link | Myntra | Tira | Blinkit |
|----------|------------|-------------|--------|------|---------|
| GC990    | https://...| https://... | https://... | https://... | https://... |

### 2. Run the script
```bash
python price_tracker.py
```

### 3. Output
- Results are saved in `Scraped_Product_Prices.xlsx`
- Errors go to `scraper.log`

---

## 🔐 Proxy Notes
- Ensure your proxy provider supports Selenium, HTTPS, and headless access
- For best results, use **rotating residential proxies** (not datacenter proxies)

---

## 🧪 Troubleshooting

| Problem                      | Solution |
|-----------------------------|----------|
| `Access Denied`             | Rotate proxy, try `undetected_chromedriver`, or add delays
| HTML is blank or blocked    | Add `print(driver.page_source)` to inspect content
| `distutils` error           | Install `setuptools`
| Anti-bot blocks on Tira     | Tira uses Akamai. Consider switching to Playwright or cloud scraping APIs

---

## 🧩 Technologies Used

| Tool                     | Purpose                          |
|--------------------------|----------------------------------|
| Python                   | Core language                    |
| Pandas                   | Excel reading/writing            |
| Selenium                 | Render dynamic pages             |
| BeautifulSoup            | Parse static HTML                |
| Requests                 | Fast static page loading         |
| Logging                  | Logs warnings & failures         |
| `undetected_chromedriver`| Bypass bot detection             |
| Proxies                  | Avoid rate limits/IP blocks      |

---

## 💡 Tips

- Don't run scraping in parallel too fast — add delays
- Log everything with `logging.info()` and `logging.error()`
- Check `scraper.log` and HTML for troubleshooting

---

## 📬 Author & Support

- Built by Lalit Thapa
- For help, raise an issue or ping me on lalitthapa2108@gmail.com or +91 9871776722

---

## 📜 License
MIT License. Free to use for personal and commercial use.

---

## 📌 Example Output

| Sku Code | Nykaa Link | Amazon Link | Myntra | Tira | Blinkit |
|----------|------------|-------------|--------|------|---------|
| GC990    | ₹716       | ₹715        | N/A    | N/A  | N/A     |

---

Enjoy tracking your product prices effortlessly! 🛍️
