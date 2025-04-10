from dataclasses import dataclass
import datetime
from enum import Enum


@dataclass
class QuotesData:
    banks_names: list[str]
    quotes: list[float]
    times: list[datetime.datetime]
    commissions: list[bool]
    currency: list[str]


class CurrencyCode(Enum):
    EUR = 2
    USD = 3
    GBP = 321
    AED = 5


class CityCode(Enum):
    MOSCOW = 1
    SPB = 2

    