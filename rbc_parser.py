from bs4 import BeautifulSoup
import requests
from datetime import datetime, date
import pytz

import logging

logger = logging.getLogger(__name__)

def time_str_to_datetime(time_str:list[str]) -> list[datetime]:
    ''' Function accepts list of time_str in format HH:MM in 24 hrs format and 
     returns list of datetime objects in format %Y-%m-%d %H:%M + Moscow timezone.
     The day is always current date because it is a real-time parser,
     timezone always Moscow TZ because we have only 2 cities SPb and Moscow '''

    today = date.today()
    moscow_tz = pytz.timezone('Europe/Moscow')

    # Strip time_str from possible spaces
    t = [x.text.strip() for x in time_str]
    
    # Converting str into datetime objects
    t_datetime = [datetime.strptime(f'{today} {x}', '%Y-%m-%d %H:%M') for x in t]

    # Adding timezone
    t_datetime = [moscow_tz.localize(x) for x in t_datetime]

    return t_datetime

def _save_to_file(file_name:str, response:str) -> str:
     with open('page.html', 'w', encoding='utf-8') as file:
        file.write(response)

def _read_from_file(file_name:str) -> str:
    with open('page.html', 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def parse_quotes(url: str, div_container:str, currency:str):

    content = requests.get(url)

    data = BeautifulSoup(content.text,'lxml')

    # _save_to_file('page1.html', content.text)

    # content_text = _read_from_file('page.html')
    # data = BeautifulSoup(content_text,'lxml')

    container = data.find('div', class_=div_container)

    banks = container.find_all('a', class_='quote__office__one__name')
    quotes = container.find_all('div', class_='quote__office__cell quote__office__one__rate quote__mode_list_view')
    times = container.find_all('div', class_='quote__office__cell quote__office__one__time')

    t_datetime = time_str_to_datetime(times)
    cleaned_banks = [x.text.strip() for x in banks]
    quotes = [x.text.strip() for x in quotes]
    comissions = [True if '%' in x else False for x in quotes]
    cleaned_quotes = [float(x.replace('%','')) for x in quotes]
    currency_list  = [currency.upper() for x in range(len(quotes))]

    return cleaned_banks, cleaned_quotes, t_datetime, comissions, currency_list
  