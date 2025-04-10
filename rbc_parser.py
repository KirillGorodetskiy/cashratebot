from bs4 import BeautifulSoup
from bs4.element import Tag
import requests
from datetime import datetime, date
import pytz
import logging
from models import QuotesData

logger = logging.getLogger(__name__)


def time_str_to_datetime(time_str: list[Tag]) -> list[datetime]:
    ''' Function accepts list of Tags with text in format HH:MM in 24 hrs format and
     returns list of datetime objects in format %Y-%m-%d %H:%M + Moscow TZ.
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


def _save_to_file(file_name: str, response: str) -> None:
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(response)


def _read_from_file(file_name: str) -> str:
    with open(file_name, 'r', encoding='utf-8') as file:
        content = file.read()
    return content


def _prepare_parsed_data(banks_raw: list[Tag], quotes_raw: list[Tag],
                         times_raw: list[Tag], currency: str):
    datetime_objects_list = time_str_to_datetime(times_raw)
    banks = [b.text.strip() for b in banks_raw]
    quotes = [q.text.strip() for q in quotes_raw]
    # On the wevsite bank offers that have additional comissions are
    # marked with % sign. So, below we create list[bool] Yes/No Flag for commissions
    commissions = [True if '%' in x else False for x in quotes]
    # Now, when we`ve extracted info about comissinos we remove % sign
    cleaned_quotes = [float(x.replace('%','')) for x in quotes]
    # create currency list for casw when our df will have several currencies
    currency_list = [currency.upper() for x in range(len(quotes))]
    return QuotesData(
        banks_names=banks,
        quotes=cleaned_quotes,
        times=datetime_objects_list,
        commissions=commissions,
        currency=currency_list,
    )


def parse_quotes(url: str, target_div_container: str, currency: str) -> QuotesData:

    content: requests.Response = requests.get(url)

    data: BeautifulSoup = BeautifulSoup(content.text, 'lxml')

    # _save_to_file('page1.html', content.text)

    # content_text = _read_from_file('page.html')
    # data = BeautifulSoup(content_text,'lxml')

    container: Tag = data.find('div', class_=target_div_container)  # tarrget_div_container contains our target table with quotes

    banks_raw: list[Tag] = container.find_all('a', class_='quote__office__one__name')
    quotes_raw: list[Tag] = container.find_all('div', class_='quote__office__cell quote__office__one__rate quote__mode_list_view')
    times_raw: list[Tag] = container.find_all('div', class_='quote__office__cell quote__office__one__time')

    prepared_quotes_data_object = _prepare_parsed_data(banks_raw, quotes_raw, times_raw, currency)

    return prepared_quotes_data_object

