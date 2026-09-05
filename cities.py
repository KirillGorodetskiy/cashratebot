from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    key: str
    rbc_id: int
    en: str
    ru: str
    button_en: str
    button_ru: str
    emoji: str


CITIES: tuple[City, ...] = (
    City('Moscow', 1, 'Moscow', 'Москва', 'Moscow', 'Москва', '🏙'),
    City(
        'SPB',
        2,
        'St. Petersburg',
        'Санкт-Петербург',
        'SPb',
        'СПб',
        '🌉',
    ),
    City(
        'Rostov',
        3,
        'Rostov Region',
        'Ростовская область',
        'Rostov',
        'Ростов',
        '🌾',
    ),
    City(
        'Kaliningrad',
        4,
        'Kaliningrad',
        'Калининград',
        'Kaliningrad',
        'Калининград',
        '⚓',
    ),
    City(
        'Krasnodar',
        5,
        'Krasnodar Region',
        'Краснодарский край',
        'Krasnodar',
        'Краснодар',
        '☀️',
    ),
    City(
        'Bashkortostan',
        6,
        'Bashkortostan',
        'Республика Башкортостан',
        'Bashkortostan',
        'Башкортостан',
        '🌿',
    ),
    City(
        'Tatarstan',
        7,
        'Tatarstan',
        'Республика Татарстан',
        'Tatarstan',
        'Татарстан',
        '🌙',
    ),
    City(
        'Volgograd',
        8,
        'Volgograd Region',
        'Волгоградская область',
        'Volgograd',
        'Волгоград',
        '🏛',
    ),
)


def city_keys() -> frozenset[str]:
    return frozenset(city.key for city in CITIES)


def city_by_key(key: str) -> City | None:
    for city in CITIES:
        if city.key == key:
            return city
    return None


def city_label(key: str, lang: str) -> str:
    city = city_by_key(key)
    if city is None:
        return key
    return city.ru if lang == 'ru' else city.en


def button_label(city: City, lang: str) -> str:
    name = city.button_ru if lang == 'ru' else city.button_en
    return f'{city.emoji} {name}'
