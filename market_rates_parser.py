from bs4 import BeautifulSoup
import requests
import logging
import time
from selenium import webdriver
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)

cbrf_url = 'https://www.cbr.ru/eng/currency_base/daily/'
trading_ecomonics_url = 'https://tradingeconomics.com/currencies?base=rub'
exchange_rates_url = 'https://www.exchangerates.org.uk/Russian-Rouble-RUB-currency-table.html'

currencies_list = ['USD', 'GBP', 'EUR', 'CNY', 'AED']

def parse_rates_cbrf():
        
    content: requests.Response = requests.get(cbrf_url)

    data: BeautifulSoup = BeautifulSoup(content.text, 'lxml')

    container: Tag = data.find('table', class_='data')

    rows = container.find_all('tr')

    currencies = {}

    for row in rows[1:]:
        columns = row.find_all('td')
        char_code = columns[1].text
        unit = int(columns[2].text)
        rate = float(columns[4].text)
        currencies[char_code] = round(rate / unit, 4)

    print(currencies)

def parse_rates_trading_economics():
        
    content: requests.Response = requests.get(trading_ecomonics_url)

    data: BeautifulSoup = BeautifulSoup(content.text, 'lxml')

    container: Tag = data.find('tdiv', class_='table table-hover sortable-theme-minimal table-heatmap table-striped')

    rows = container.find_all('tr')

    currencies = {}

    for row in rows[1:]:
        columns = row.find_all('td')
        char_code = columns[1].text
        unit = int(columns[2].text)
        rate = float(columns[4].text)
        currencies[char_code] = round(rate / unit, 4)

    print(currencies)

def parse_rates_exchangerates():
    
    # Setup Chrome options for stealth headless mode
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")  # <- Better detection bypass
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    # Optional: disable image loading (faster + stealthier)
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    # You might need to match your installed Chrome version
    driver = uc.Chrome(options=options, headless=True, version_main=135)  # replace with your actual Chrome major version

    driver.get(exchange_rates_url)
    # Wait for JavaScript to load
    time.sleep(1)  # Adjust time if needed
    # Get HTML content
    html = driver.page_source
        
    data: BeautifulSoup = BeautifulSoup(html, 'lxml')
    container: Tag = data.find('div', class_='css-panes')
    rows = container.find_all('tr', class_=lambda c: c and 'col' in c)
    currencies = {}
    for row in rows[1:]:
        columns = row.find_all('td')
        char_code = columns[5].text[4:]
        rate = float(columns[7].text)
        currencies[char_code] = round(rate, 4)
    # Do your parsing logic
    
    driver.quit()
    print(currencies)
    print(len(currencies))

def main():
       

if __name__ == '__main__':
    main()

