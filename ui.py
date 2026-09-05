from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from calculator import parse_amount
from cities import CITIES, button_label, city_keys
from currencies import CURRENCIES, currency_keys


ALLOWED_CITIES = city_keys()
ALLOWED_CURRENCIES = currency_keys()
ALLOWED_MODES = frozenset({'cash', 'usdt'})
ALLOWED_ALERT_DIRS = frozenset({'below', 'above'})
CALC_PRESETS = (100, 500, 1000, 5000)

LABEL_CASH = {'en': '💵 Cash', 'ru': '💵 Наличные'}
LABEL_USDT = {'en': '💰 USDT', 'ru': '💰 USDT'}
LABEL_HOME = {'en': '🏠 Menu', 'ru': '🏠 Меню'}
LABEL_BACK = {'en': '⬅️ Back', 'ru': '⬅️ Назад'}
LABEL_REFRESH = {'en': '🔄 Refresh', 'ru': '🔄 Обновить'}
LABEL_STATS = {
    'en': '📊 All currencies',
    'ru': '📊 Все валюты',
}
LABEL_CALC = {'en': '🧮 Amount', 'ru': '🧮 Сумма'}
LABEL_ALERT = {'en': '🔔 Alert', 'ru': '🔔 Алерт'}
LABEL_FAV = {'en': '★ Favorite', 'ru': '★ Избранное'}
LABEL_WHERE = {'en': '📍 Offices', 'ru': '📍 Офисы'}
LABEL_ALERTS = {'en': '🔔 Alerts', 'ru': '🔔 Алерты'}
LABEL_BELOW = {'en': 'Below', 'ru': 'Ниже'}
LABEL_ABOVE = {'en': 'Above', 'ru': 'Выше'}
TOAST_INVALID = {
    'en': 'Invalid choice',
    'ru': 'Некорректный выбор',
}
TOAST_REFRESH = {'en': 'Updating…', 'ru': 'Обновляю…'}
TOAST_HOME = {'en': 'Main menu', 'ru': 'Главное меню'}
TOAST_SAVED = {'en': 'Saved', 'ru': 'Сохранено'}
TOAST_ALERT = {'en': 'Alert created', 'ru': 'Алерт создан'}
TOAST_ALERT_LIMIT = {
    'en': 'Alert limit reached',
    'ru': 'Лимит алертов',
}

BACK_STEPS = {
    'cities': 'home',
    'currencies': 'cities',
    'quotes': 'currencies',
    'stats': 'currencies',
    'usdt': 'home',
    'home': 'home',
    'calc': 'quotes',
    'calc_wait': 'quotes',
    'alert': 'quotes',
    'offices': 'quotes',
    'office': 'offices',
    'alerts': 'home',
}


def resolve_lang(language_code: str | None) -> str:
    if language_code and language_code.startswith('ru'):
        return 'ru'
    return 'en'


def parse_city(callback_data: str) -> str | None:
    if ':' not in callback_data:
        return None
    city = callback_data.split(':', 1)[1]
    if city not in ALLOWED_CITIES:
        return None
    return city


def parse_currency(callback_data: str) -> str | None:
    if ':' not in callback_data:
        return None
    currency = callback_data.split(':', 1)[1]
    if currency not in ALLOWED_CURRENCIES:
        return None
    return currency


def parse_mode(callback_data: str) -> str | None:
    if ':' not in callback_data:
        return None
    mode = callback_data.split(':', 1)[1]
    if mode not in ALLOWED_MODES:
        return None
    return mode


def parse_alert_dir(callback_data: str) -> str | None:
    if not callback_data.startswith('alert:dir:'):
        return None
    direction = callback_data.split(':', 2)[2]
    if direction not in ALLOWED_ALERT_DIRS:
        return None
    return direction


def parse_threshold(callback_data: str) -> float | None:
    if not callback_data.startswith('alert:th:'):
        return None
    return parse_amount(callback_data.split(':', 2)[2])


def parse_calc_preset(callback_data: str) -> float | None:
    if not callback_data.startswith('calc:'):
        return None
    raw = callback_data.split(':', 1)[1]
    if raw == 'open':
        return None
    return parse_amount(raw)


def parse_alert_id(callback_data: str) -> int | None:
    if not callback_data.startswith('alert:del:'):
        return None
    raw = callback_data.split(':', 2)[2]
    if not raw.isdigit():
        return None
    return int(raw)


def parse_office_id(callback_data: str) -> str | None:
    if not callback_data.startswith('office:'):
        return None
    from office_info import parse_bank_id
    return parse_bank_id(callback_data.split(':', 1)[1])


def _nav_row(lang: str, refresh: bool = False) -> list:
    row = [
        InlineKeyboardButton(
            LABEL_BACK[lang],
            callback_data='nav:back',
        ),
        InlineKeyboardButton(
            LABEL_HOME[lang],
            callback_data='nav:home',
        ),
    ]
    if refresh:
        row.insert(
            0,
            InlineKeyboardButton(
                LABEL_REFRESH[lang],
                callback_data='nav:refresh',
            ),
        )
    return row


def home_inline_keyboard(
    lang: str,
    prefs: dict | None = None,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                LABEL_CASH[lang],
                callback_data='mode:cash',
            ),
            InlineKeyboardButton(
                LABEL_USDT[lang],
                callback_data='mode:usdt',
            ),
        ],
    ]
    prefs = prefs or {}
    last_city = prefs.get('last_city')
    last_ccy = prefs.get('last_currency')
    if last_city in ALLOWED_CITIES and last_ccy in ALLOWED_CURRENCIES:
        label = f'↩ {last_city} {last_ccy}'
        rows.append([
            InlineKeyboardButton(label, callback_data='last:open'),
        ])
    fav_city = prefs.get('fav_city')
    fav_ccy = prefs.get('fav_currency')
    if fav_city in ALLOWED_CITIES and fav_ccy in ALLOWED_CURRENCIES:
        label = f'★ {fav_city} {fav_ccy}'
        rows.append([
            InlineKeyboardButton(label, callback_data='fav:open'),
        ])
    rows.append([
        InlineKeyboardButton(
            LABEL_ALERTS[lang],
            callback_data='alerts:list',
        ),
    ])
    return InlineKeyboardMarkup(rows)


def cities_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    current: list[InlineKeyboardButton] = []
    for city in CITIES:
        current.append(
            InlineKeyboardButton(
                button_label(city, lang),
                callback_data=f'city:{city.key}',
            )
        )
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    rows.append(_nav_row(lang))
    return InlineKeyboardMarkup(rows)


def currencies_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    current: list[InlineKeyboardButton] = []
    for item in CURRENCIES:
        current.append(
            InlineKeyboardButton(
                item.button,
                callback_data=f'currency:{item.key}',
            )
        )
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    rows.append([
        InlineKeyboardButton(
            LABEL_STATS[lang],
            callback_data='stats',
        ),
    ])
    rows.append(_nav_row(lang))
    return InlineKeyboardMarkup(rows)


def nav_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([_nav_row(lang)])


def result_inline_keyboard(
    lang: str,
    kind: str = 'quotes',
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if kind == 'quotes':
        rows.append([
            InlineKeyboardButton(
                LABEL_CALC[lang],
                callback_data='calc:open',
            ),
            InlineKeyboardButton(
                LABEL_ALERT[lang],
                callback_data='alert:open',
            ),
        ])
        rows.append([
            InlineKeyboardButton(
                LABEL_FAV[lang],
                callback_data='fav:set',
            ),
            InlineKeyboardButton(
                LABEL_WHERE[lang],
                callback_data='where:open',
            ),
        ])
    elif kind == 'usdt':
        rows.append([
            InlineKeyboardButton(
                LABEL_ALERT[lang],
                callback_data='alert:open',
            ),
        ])
    rows.append(_nav_row(lang, refresh=True))
    return InlineKeyboardMarkup(rows)


def calc_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                str(amount),
                callback_data=f'calc:{amount}',
            )
            for amount in CALC_PRESETS
        ],
        _nav_row(lang),
    ]
    return InlineKeyboardMarkup(rows)


def alert_dir_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                LABEL_BELOW[lang],
                callback_data='alert:dir:below',
            ),
            InlineKeyboardButton(
                LABEL_ABOVE[lang],
                callback_data='alert:dir:above',
            ),
        ],
        _nav_row(lang),
    ])


def alert_threshold_keyboard(
    rate: float,
    lang: str,
) -> InlineKeyboardMarkup:
    values = [
        round(rate - 1, 2),
        round(rate - 0.5, 2),
        round(rate, 2),
        round(rate + 0.5, 2),
        round(rate + 1, 2),
    ]
    rows: list[list[InlineKeyboardButton]] = []
    current: list[InlineKeyboardButton] = []
    for value in values:
        if value <= 0:
            continue
        current.append(
            InlineKeyboardButton(
                f'{value:.2f}',
                callback_data=f'alert:th:{value:.2f}',
            )
        )
        if len(current) == 3:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    rows.append(_nav_row(lang))
    return InlineKeyboardMarkup(rows)


def offices_keyboard(
    offices: list[tuple[str, str]],
    lang: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for bank_id, name in offices:
        label = name if len(name) <= 28 else name[:27] + '…'
        rows.append([
            InlineKeyboardButton(
                label,
                callback_data=f'office:{bank_id}',
            ),
        ])
    rows.append(_nav_row(lang))
    return InlineKeyboardMarkup(rows)


def alerts_list_keyboard(
    alerts: list[dict],
    lang: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for item in alerts:
        target = item.get('currency') or 'USDT'
        city = item.get('city') or ''
        label = (
            f'✕ {target} {city} {item["direction"]} '
            f'{item["threshold"]:.2f}'
        )
        rows.append([
            InlineKeyboardButton(
                label[:64],
                callback_data=f'alert:del:{item["id"]}',
            ),
        ])
    rows.append(_nav_row(lang))
    return InlineKeyboardMarkup(rows)


BOT_SHORT_DESCRIPTION = {
    'en': 'Cash FX and USDT/RUB rates in Russian cities',
    'ru': 'Наличные курсы и USDT/RUB в городах России',
}

BOT_DESCRIPTION = {
    'en': (
        'Live cash exchange rates from cash.rbc.ru for Moscow, '
        'St. Petersburg and other regions, plus USDT/RUB from '
        'several public sources. Offers are not always final — '
        'confirm with the bank before visiting.'
    ),
    'ru': (
        'Актуальные наличные курсы с cash.rbc.ru для Москвы, '
        'Санкт-Петербурга и других регионов, плюс USDT/RUB из '
        'нескольких открытых источников. Предложения не всегда '
        'окончательные — уточните условия в банке.'
    ),
}


def bot_commands(lang: str) -> list[BotCommand]:
    if lang == 'ru':
        return [
            BotCommand('start', 'Открыть главное меню'),
            BotCommand('cash', 'Наличные курсы'),
            BotCommand('usdt', 'Курс USDT к рублю'),
            BotCommand('help', 'Как пользоваться ботом'),
        ]
    return [
        BotCommand('start', 'Open the main menu'),
        BotCommand('cash', 'Cash currency rates'),
        BotCommand('usdt', 'USDT to RUB rates'),
        BotCommand('help', 'How to use the bot'),
    ]
