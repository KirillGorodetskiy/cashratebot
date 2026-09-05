from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from cities import CITIES, button_label, city_keys


ALLOWED_CITIES = city_keys()
ALLOWED_CURRENCIES = frozenset({'USD', 'EUR', 'GBP', 'AED'})
ALLOWED_MODES = frozenset({'cash', 'usdt'})

LABEL_CASH = {'en': '💵 Cash', 'ru': '💵 Наличные'}
LABEL_USDT = {'en': '💰 USDT', 'ru': '💰 USDT'}
LABEL_HOME = {'en': '🏠 Menu', 'ru': '🏠 Меню'}
LABEL_BACK = {'en': '⬅️ Back', 'ru': '⬅️ Назад'}
LABEL_REFRESH = {'en': '🔄 Refresh', 'ru': '🔄 Обновить'}
LABEL_STATS = {
    'en': '📊 All currencies',
    'ru': '📊 Все валюты',
}
TOAST_INVALID = {
    'en': 'Invalid choice',
    'ru': 'Некорректный выбор',
}
TOAST_REFRESH = {'en': 'Updating…', 'ru': 'Обновляю…'}
TOAST_HOME = {'en': 'Main menu', 'ru': 'Главное меню'}

BACK_STEPS = {
    'cities': 'home',
    'currencies': 'cities',
    'quotes': 'currencies',
    'stats': 'currencies',
    'usdt': 'home',
    'home': 'home',
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


def home_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
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
    ])


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
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('💵 USD', callback_data='currency:USD'),
            InlineKeyboardButton('💶 EUR', callback_data='currency:EUR'),
        ],
        [
            InlineKeyboardButton('💷 GBP', callback_data='currency:GBP'),
            InlineKeyboardButton('💴 AED', callback_data='currency:AED'),
        ],
        [
            InlineKeyboardButton(
                LABEL_STATS[lang],
                callback_data='stats',
            ),
        ],
        _nav_row(lang),
    ])


def result_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([_nav_row(lang, refresh=True)])


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
