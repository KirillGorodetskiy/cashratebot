prompt_messages_greeting = {
    'en': (
        '<b>Cash and USDT rates</b>\n'
        '<blockquote expandable>Data from cash.rbc.ru. Bank offers '
        'are not always final — confirm with the bank before '
        'visiting.</blockquote>\n'
        'Choose cash or USDT:'
    ),
    'ru': (
        '<b>Курсы наличных и USDT</b>\n'
        '<blockquote expandable>Данные с cash.rbc.ru. Предложения '
        'банков не всегда окончательные — уточните условия в '
        'банке перед визитом.</blockquote>\n'
        'Выберите наличные или USDT:'
    ),
}

prompt_messages_cities = {
    'en': '<b>Cash</b>\nChoose your city:',
    'ru': '<b>Наличные</b>\nВыберите город:',
}

prompt_messages_currencies = {
    'en': (
        '<b>Cash · {city}</b>\n'
        'Top-{num_of_banks} quotes or city stats:'
    ),
    'ru': (
        '<b>Наличные · {city}</b>\n'
        'Топ-{num_of_banks} курсов или статистика:'
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

prompt_help = {
    'en': (
        '<b>How to use</b>\n'
        '• <b>Cash</b> — city, then currency or city stats\n'
        '• <b>USDT</b> — live USDT/RUB from several sources\n'
        '• Last / Favorite reopen a pair in one tap\n'
        '• Amount, Alert, and Offices on a rate card\n'
        '• Share via inline: <code>@bot Moscow USD</code> '
        'or <code>@bot usdt</code>\n'
        'Use Back, Home, and Refresh on the card.'
    ),
    'ru': (
        '<b>Как пользоваться</b>\n'
        '• <b>Наличные</b> — город, затем валюта или статистика\n'
        '• <b>USDT</b> — актуальный курс USDT/RUB\n'
        '• Последний / Избранное открывают пару одним нажатием\n'
        '• Сумма, алерт и офисы на карточке курса\n'
        '• Шаринг: <code>@bot Moscow USD</code> или '
        '<code>@bot usdt</code>\n'
        'Используйте Назад, Меню и Обновить на карточке.'
    ),
}

prompt_calc = {
    'en': (
        '<b>Amount</b>\n'
        'Choose a preset or send a number in the chat.'
    ),
    'ru': (
        '<b>Сумма</b>\n'
        'Выберите значение или отправьте число в чат.'
    ),
}

prompt_alert = {
    'en': '<b>Alert</b>\nNotify me when the rate is:',
    'ru': '<b>Алерт</b>\nСообщить, когда курс будет:',
}

prompt_alert_th = {
    'en': '<b>Alert</b>\nChoose a threshold around {rate:.2f}:',
    'ru': '<b>Алерт</b>\nПорог около {rate:.2f}:',
}

prompt_alerts_empty = {
    'en': '<b>Alerts</b>\nYou have no alerts yet.',
    'ru': '<b>Алерты</b>\nПока нет алертов.',
}

prompt_alerts_list = {
    'en': '<b>Alerts</b>\nTap an item to delete it.',
    'ru': '<b>Алерты</b>\nНажмите, чтобы удалить.',
}

prompt_offices = {
    'en': '<b>Offices</b>\nChoose a bank for address and phone:',
    'ru': '<b>Офисы</b>\nВыберите банк для адреса и телефона:',
}

prompt_no_offices = {
    'en': 'No office details are available for these quotes.',
    'ru': 'Для этих курсов нет данных об офисах.',
}

prompt_inline_hint = {
    'en': 'Type a city and currency, e.g. Moscow USD, or usdt',
    'ru': 'Напишите город и валюту, например Moscow USD, или usdt',
}

cities_prompt = {
    'MOSCOW': {'en': 'Moscow', 'ru': 'Москва'},
    'SPB': {'en': 'St. Petersburg', 'ru': 'Санкт-Петербург'},
    'ROSTOV': {
        'en': 'Rostov Region',
        'ru': 'Ростовская область',
    },
    'KALININGRAD': {
        'en': 'Kaliningrad',
        'ru': 'Калининград',
    },
    'KRASNODAR': {
        'en': 'Krasnodar Region',
        'ru': 'Краснодарский край',
    },
    'BASHKORTOSTAN': {
        'en': 'Bashkortostan',
        'ru': 'Республика Башкортостан',
    },
    'TATARSTAN': {
        'en': 'Tatarstan',
        'ru': 'Республика Татарстан',
    },
    'VOLGOGRAD': {
        'en': 'Volgograd Region',
        'ru': 'Волгоградская область',
    },
}
