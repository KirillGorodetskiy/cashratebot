import html
import json
import logging
import re

import requests

import redis_client

logger = logging.getLogger(__name__)

BANK_INFO_URL = 'https://cash.rbc.ru/cash/json/cash_bank_info/'
CACHE_TTL = 86400


def parse_bank_id(raw: str) -> str | None:
    if not raw or not re.fullmatch(r'\d{1,12}', raw):
        return None
    return raw


def parse_bank_info(payload: dict) -> dict[str, str]:
    info = payload.get('bank', {}).get('info', {})
    metro = ''
    metro_raw = info.get('metro')
    if isinstance(metro_raw, list) and metro_raw:
        first = metro_raw[0]
        if isinstance(first, list) and first:
            metro = str(first[0])
        elif isinstance(first, str):
            metro = first
    return {
        'name': str(info.get('bank_name') or ''),
        'phone': str(info.get('tel') or ''),
        'address': str(info.get('address') or ''),
        'metro': metro,
        'city': str(info.get('city_name') or ''),
    }


def format_office(info: dict[str, str], lang: str) -> str:
    name = html.escape(info.get('name') or '—', quote=True)
    phone = html.escape(info.get('phone') or '—', quote=True)
    address = html.escape(info.get('address') or '—', quote=True)
    metro = html.escape(info.get('metro') or '—', quote=True)
    if lang == 'ru':
        return (
            f'<b>{name}</b>\n'
            f'Метро: {metro}\n'
            f'Телефон: {phone}\n'
            f'Адрес: {address}'
        )
    return (
        f'<b>{name}</b>\n'
        f'Metro: {metro}\n'
        f'Phone: {phone}\n'
        f'Address: {address}'
    )


def fetch_bank_info(bank_id: str) -> dict[str, str] | None:
    parsed_id = parse_bank_id(bank_id)
    if parsed_id is None:
        return None
    cache_key = f'bank:info:{parsed_id}'
    if redis_client.REDIS_AVAILABLE and redis_client.REDIS_CLIENT:
        try:
            cached = redis_client.REDIS_CLIENT.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as exc:
            logger.error('Could not read bank cache: %s', exc)
    try:
        response = requests.get(
            BANK_INFO_URL,
            params={'bank_id': parsed_id},
            timeout=15,
        )
        response.raise_for_status()
        info = parse_bank_info(response.json())
    except Exception as exc:
        logger.error('Could not fetch bank %s: %s', parsed_id, exc)
        return None
    if redis_client.REDIS_AVAILABLE and redis_client.REDIS_CLIENT:
        try:
            redis_client.REDIS_CLIENT.setex(
                cache_key,
                CACHE_TTL,
                json.dumps(info, ensure_ascii=False),
            )
        except Exception as exc:
            logger.error('Could not save bank cache: %s', exc)
    return info
