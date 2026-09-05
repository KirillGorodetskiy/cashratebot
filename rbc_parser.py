from bs4 import BeautifulSoup
from bs4.element import Tag
import requests
from datetime import datetime, date
import re
import pytz
import logging
from models import QuotesData

logger = logging.getLogger(__name__)


def time_str_to_datetime(time_str: list[Tag]) -> list[datetime]:
    ''' Function accepts list of Tags with text in format HH:MM in 24 hrs format and
     returns list of datetime objects in format %Y-%m-%d %H:%M + Moscow TZ.
     The day is always current date because it is a real-time parser,
     timezone always Moscow TZ because we have only 2 cities SPb and Moscow '''

    return _times_from_strings([item.text.strip() for item in time_str])


def _times_from_strings(values: list[str]) -> list[datetime]:
    today = date.today()
    moscow_tz = pytz.timezone('Europe/Moscow')
    parsed: list[datetime] = []
    for raw in values:
        value = datetime.strptime(
            f'{today} {raw.strip()}',
            '%Y-%m-%d %H:%M',
        )
        parsed.append(moscow_tz.localize(value))
    return parsed


def _save_to_file(file_name: str, response: str) -> None:
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(response)


def _read_from_file(file_name: str) -> str:
    with open(file_name, 'r', encoding='utf-8') as file:
        content = file.read()
    return content


def _empty_quotes() -> QuotesData:
    return QuotesData(
        banks_names=[],
        quotes=[],
        times=[],
        commissions=[],
        currency=[],
        bank_ids=[],
        metros=[],
        phones=[],
    )


def _office_metro(office: Tag) -> str:
    metro = office.find('div', class_='quote__office__one__metro')
    if metro is None:
        return ''
    for span in metro.find_all('span'):
        classes = span.get('class') or []
        if 'quote__office__metro__distance' in classes:
            continue
        name = span.get_text(strip=True)
        if name:
            return name
    return ''


def _office_bank_id(office: Tag) -> str:
    link = office.find('a', class_='quote__office__one__name')
    if link is None or not link.get('href'):
        return ''
    match = re.search(r'/bank/(\d+)', link['href'])
    if match is None:
        return ''
    return match.group(1)


def parse_quotes(url: str, target_div_container: str,
                 currency: str) -> QuotesData:
    try:
        content = requests.get(url, timeout=15)
        content.raise_for_status()
    except requests.RequestException as exc:
        logger.error('Could not fetch quotes from %s: %s', url, exc)
        return _empty_quotes()

    data: BeautifulSoup = BeautifulSoup(content.text, 'lxml')
    container = data.find('div', class_=target_div_container)
    if container is None:
        logger.warning('No quotes table for %s', url)
        return _empty_quotes()

    offices = container.find_all('div', class_='js-one-office')
    if not offices:
        logger.warning('Empty quotes table for %s', url)
        return _empty_quotes()

    try:
        return _parse_offices(offices, currency)
    except Exception as exc:
        logger.error('Could not parse quotes from %s: %s', url, exc)
        return _empty_quotes()


def _parse_offices(offices: list[Tag], currency: str) -> QuotesData:
    banks: list[str] = []
    quotes: list[float] = []
    times_raw: list[str] = []
    commissions: list[bool] = []
    bank_ids: list[str] = []
    metros: list[str] = []
    phones: list[str] = []

    for office in offices:
        name_el = office.find(class_='quote__office__one__name')
        rate_el = office.find(
            'div',
            class_=lambda value: (
                bool(value) and 'quote__office__one__rate' in value
            ),
        )
        time_el = office.find(
            'div',
            class_=lambda value: (
                bool(value) and 'quote__office__one__time' in value
            ),
        )
        if name_el is None or rate_el is None or time_el is None:
            continue
        rate_text = rate_el.get_text(strip=True)
        has_fee = '%' in rate_text
        try:
            quote = float(rate_text.replace('%', '').replace(',', '.'))
        except ValueError:
            continue
        phone_el = office.find(class_='quote__office__one__phone')
        banks.append(name_el.get_text(strip=True))
        quotes.append(quote)
        times_raw.append(time_el.get_text(strip=True))
        commissions.append(has_fee)
        bank_ids.append(_office_bank_id(office))
        metros.append(_office_metro(office))
        phones.append(
            phone_el.get_text(strip=True) if phone_el else ''
        )

    if not banks:
        return _empty_quotes()

    return QuotesData(
        banks_names=banks,
        quotes=quotes,
        times=_times_from_strings(times_raw),
        commissions=commissions,
        currency=[currency.upper() for _ in banks],
        bank_ids=bank_ids,
        metros=metros,
        phones=phones,
    )
