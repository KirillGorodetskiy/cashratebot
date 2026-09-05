import html
import re
import statistics

import requests

from data_formatter import card_header

MIN_SOURCES = 2
MIN_RATE = 50
MAX_RATE = 150

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/json,*/*",
}

def validate(rate):
    rate = float(rate)
    if not MIN_RATE <= rate <= MAX_RATE:
        raise ValueError(f"Suspicious rate: {rate}")
    return rate

def get_html(url):
    r = requests.get(url, headers=HEADERS, timeout=12)
    r.raise_for_status()
    return re.sub(r"\s+", " ", r.text)

def extract(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            return validate(m.group(1).replace(",", "."))
    raise ValueError("Rate not found")

def fetch_coinbase():
    r = requests.get(
        "https://api.coinbase.com/v2/exchange-rates",
        params={"currency": "USDT"},
        headers=HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    return validate(r.json()["data"]["rates"]["RUB"])

def fetch_coingecko():
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "tether", "vs_currencies": "rub"},
        headers=HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    return validate(r.json()["tether"]["rub"])

def fetch_bybit():
    text = get_html("https://www.bybit.com/en/convert/usdt-to-rub/1/")
    return extract(text, [
        r"current exchange rate is\s*1\s*USDT\s*=\s*₽\s*([0-9]+(?:[.,][0-9]+)?)",
        r"1\s*USDT\s*≈\s*₽\s*([0-9]+(?:[.,][0-9]+)?)",
        r"1\s*USDT\s*=\s*₽\s*([0-9]+(?:[.,][0-9]+)?)",
    ])

def fetch_coinmarketcap():
    text = get_html(
        "https://coinmarketcap.com/currencies/tether/usdt/rub/"
    )
    return extract(text, [
        r"conversion rate today is\s*₽\s*([0-9]+(?:[.,][0-9]+)?)",
        r"real-time conversion rate.*?is\s*₽\s*([0-9]+(?:[.,][0-9]+)?)",
        r"1\s*USDT\s*=\s*₽\s*([0-9]+(?:[.,][0-9]+)?)",
    ])

def fetch_bitget():
    text = get_html("https://www.bitget.com/price/tether/rub")
    return extract(text, [
        r"1\s*Tether\s+USDt\s*\(USDT\)\s*equals\s*([0-9]+(?:[.,][0-9]+)?)\s*Russian\s+Ruble",
        r"1\s*USDT\s*=\s*([0-9]+(?:[.,][0-9]+)?)\s*RUB",
        r"1\s*USDT\s+is\s+currently\s+valued\s+at\s*([0-9]+(?:[.,][0-9]+)?)\s*RUB",
    ])

def fetch_coindaily():
    text = get_html(
        "https://coindaily.ru/konverter/usdt-rub/1-usdt/"
    )
    return extract(text, [
        r"1\s*USDT\s*=\s*([0-9]+(?:[.,][0-9]+)?)\s*₽",
    ])

def fetch_usdt_rub_rates():
    sources = {
        "Coinbase": fetch_coinbase,
        "CoinGecko": fetch_coingecko,
        "Bybit": fetch_bybit,
        "CoinMarketCap": fetch_coinmarketcap,
        "Bitget": fetch_bitget,
        "CoinDaily": fetch_coindaily,
    }

    rates = {}

    for name, func in sources.items():
        try:
            rate = func()
            rates[name] = rate
            print(f"✅ {name}: {rate:.2f} RUB")
        except Exception as e:
            print(f"❌ {name}: {e}")

    if len(rates) < MIN_SOURCES:
        return None

    values = list(rates.values())

    return {
        "rates": rates,
        "average": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "count": len(rates),
        "total": len(sources),
    }

def build_message(result, lang='ru'):
    if not result:
        return (
            '❌ Недостаточно данных для расчёта курса.'
            if lang == 'ru'
            else '❌ Not enough data to calculate the exchange rate.'
        )

    header = card_header(['USDT / RUB'], lang)
    table_lines = []
    for name, rate in result['rates'].items():
        table_lines.append(f'{name:<14} {rate:6.2f}')
    table_lines.append('')
    table_lines.append(f"{'Average':<14} {result['average']:6.2f}")
    table = html.escape('\n'.join(table_lines), quote=True)

    if lang == 'ru':
        extra = (
            f"Медиана {result['median']:.2f} · "
            f"диапазон {result['min']:.2f}–{result['max']:.2f} · "
            f"источники {result['count']}/{result['total']}"
        )
    else:
        extra = (
            f"Median {result['median']:.2f} · "
            f"range {result['min']:.2f}–{result['max']:.2f} · "
            f"sources {result['count']}/{result['total']}"
        )

    return (
        f'{header}'
        f'<pre>{table}</pre>\n'
        f'<blockquote expandable>{extra}</blockquote>'
    )

if __name__ == "__main__":
    result = fetch_usdt_rub_rates()
    print()
    print(build_message(result))