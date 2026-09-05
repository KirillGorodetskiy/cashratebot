from cities import CITIES
from currencies import currency_keys


CITY_ALIASES = {
    'moscow': 'Moscow',
    'москва': 'Moscow',
    'spb': 'SPB',
    'spb.': 'SPB',
    'питер': 'SPB',
    'спб': 'SPB',
    'петербург': 'SPB',
    'rostov': 'Rostov',
    'ростов': 'Rostov',
    'kaliningrad': 'Kaliningrad',
    'калининград': 'Kaliningrad',
    'krasnodar': 'Krasnodar',
    'краснодар': 'Krasnodar',
    'bashkortostan': 'Bashkortostan',
    'башкортостан': 'Bashkortostan',
    'tatarstan': 'Tatarstan',
    'татарстан': 'Tatarstan',
    'казань': 'Tatarstan',
    'volgograd': 'Volgograd',
    'волгоград': 'Volgograd',
}


def parse_inline_query(text: str) -> dict | None:
    parts = text.strip().lower().split()
    if not parts:
        return None
    if parts[0] in {'usdt', 'юсдт'}:
        return {'kind': 'usdt'}
    if len(parts) < 2:
        return None
    city = CITY_ALIASES.get(parts[0])
    if city is None:
        for item in CITIES:
            if parts[0] in {
                item.key.lower(),
                item.en.lower(),
                item.ru.lower(),
                item.button_en.lower(),
                item.button_ru.lower(),
            }:
                city = item.key
                break
    currency = parts[1].upper()
    if city is None or currency not in currency_keys():
        return None
    return {
        'kind': 'cash',
        'city': city,
        'currency': currency,
    }
