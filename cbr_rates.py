import json
import logging
import xml.etree.ElementTree as Et

import requests

import redis_client

logger = logging.getLogger(__name__)

CBR_URL = 'https://www.cbr.ru/scripts/XML_daily.asp'
CACHE_KEY = 'cbr:daily'
CACHE_TTL = 3600


def parse_cbr_xml(xml_text: str) -> dict[str, float]:
    rates: dict[str, float] = {}
    root = Et.fromstring(xml_text)
    for valute in root.findall('Valute'):
        code_el = valute.find('CharCode')
        nom_el = valute.find('Nominal')
        value_el = valute.find('Value')
        if code_el is None or nom_el is None or value_el is None:
            continue
        if not code_el.text or not nom_el.text or not value_el.text:
            continue
        nominal = float(nom_el.text.replace(',', '.'))
        value = float(value_el.text.replace(',', '.'))
        if nominal == 0:
            continue
        rates[code_el.text] = round(value / nominal, 4)
    return rates


def fetch_cbr_rates() -> dict[str, float]:
    if redis_client.REDIS_AVAILABLE and redis_client.REDIS_CLIENT:
        try:
            cached = redis_client.REDIS_CLIENT.get(CACHE_KEY)
            if cached:
                return json.loads(cached)
        except Exception as exc:
            logger.error('Could not read CBR cache: %s', exc)
    try:
        response = requests.get(CBR_URL, timeout=15)
        response.raise_for_status()
        rates = parse_cbr_xml(response.content.decode('windows-1251'))
    except Exception as exc:
        logger.error('Could not fetch CBR rates: %s', exc)
        return {}
    if redis_client.REDIS_AVAILABLE and redis_client.REDIS_CLIENT:
        try:
            redis_client.REDIS_CLIENT.setex(
                CACHE_KEY,
                CACHE_TTL,
                json.dumps(rates),
            )
        except Exception as exc:
            logger.error('Could not save CBR cache: %s', exc)
    return rates


def format_cbr_line(lang: str, cbr: float, cash: float) -> str:
    premium = ((cash / cbr) - 1) * 100 if cbr else 0
    sign = '+' if premium >= 0 else ''
    if lang == 'ru':
        return (
            f'ЦБ {cbr:.2f} · нал. {cash:.2f} · '
            f'{sign}{premium:.2f}%'
        )
    return (
        f'CBR {cbr:.2f} · cash {cash:.2f} · '
        f'{sign}{premium:.2f}%'
    )


def cbr_compare_line(currency: str, cash_buy: float, lang: str) -> str:
    rates = fetch_cbr_rates()
    cbr = rates.get(currency.upper())
    if cbr is None or not cash_buy:
        return ''
    return format_cbr_line(lang, cbr, cash_buy)
