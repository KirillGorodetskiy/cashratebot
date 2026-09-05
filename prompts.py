prompt_messages_greeting = {
    'en': (
        '<b>Cash and USDT rates</b>\n'
        '<blockquote>Data from cash.rbc.ru. Bank offers are not '
        'always final — confirm with the bank before visiting.'
        '</blockquote>\n'
        'Choose cash or USDT:'
    ),
    'ru': (
        '<b>Курсы наличных и USDT</b>\n'
        '<blockquote>Данные с cash.rbc.ru. Предложения банков не '
        'всегда окончательные — уточните условия в банке перед '
        'визитом.</blockquote>\n'
        'Выберите наличные или USDT:'
    ),
}

prompt_messages_cities = {
    'en': '<b>Choose your city</b>',
    'ru': '<b>Выберите город</b>',
}

prompt_messages_currencies = {
    'en': (
        '<b>{city}</b>\n'
        'Choose a currency for the top-{num_of_banks} bank quotes, '
        'or open city stats:'
    ),
    'ru': (
        '<b>{city}</b>\n'
        'Выберите валюту для топ-{num_of_banks} предложений банков '
        'или откройте статистику по городу:'
    ),
}

prompt_choose_city_first = {
    'en': (
        'A city has not been chosen. Use Back or /start.'
    ),
    'ru': (
        'Город не выбран. Нажмите «Назад» или /start.'
    ),
}

prompt_messages_show_data = {
    'en': '<b>{currency}</b> in <b>{city}</b>\n\n',
    'ru': '<b>{currency}</b> в городе <b>{city}</b>\n\n',
}

prompt_messages_no_data = {
    'en': 'There are no quotes available in this city right now.',
    'ru': 'Сейчас в этом городе нет доступных предложений.',
}

prompt_messages_error = {
    'en': 'Could not load rates. Please try again.',
    'ru': 'Не удалось загрузить курсы. Попробуйте ещё раз.',
}

prompt_menu_attached = {
    'en': 'Quick menu is pinned below.',
    'ru': 'Быстрое меню закреплено внизу.',
}

prompt_help = {
    'en': (
        '<b>How to use</b>\n'
        '• <b>Cash</b> — choose a city, then a currency or city stats\n'
        '• <b>USDT</b> — live USDT/RUB from several sources\n'
        'Use Back, Home, Refresh, or the pinned menu.'
    ),
    'ru': (
        '<b>Как пользоваться</b>\n'
        '• <b>Наличные</b> — выберите город, затем валюту или '
        'статистику\n'
        '• <b>USDT</b> — актуальный курс USDT/RUB из нескольких '
        'источников\n'
        'Используйте Назад, Меню, Обновить или закреплённое меню.'
    ),
}

cities_prompt = {
    'MOSCOW': {'en': 'Moscow', 'ru': 'Москва'},
    'SPB': {'en': 'St. Petersburg', 'ru': 'Санкт-Петербург'},
}
