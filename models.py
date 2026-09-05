from dataclasses import dataclass
import datetime
from enum import Enum
from typing import TypedDict, Optional


@dataclass
class QuotesData:
    banks_names: list[str]
    quotes: list[float]
    times: list[datetime.datetime]
    commissions: list[bool]
    currency: list[str]
    bank_ids: list[str]
    metros: list[str]
    phones: list[str]


class CurrencyCode(Enum):
    EUR = 2
    USD = 3
    GBP = 321
    AED = 5
    CNY = 423
    CHF = 305
    TRY = 307


class CityCode(Enum):
    MOSCOW = 1
    SPB = 2
    ROSTOV = 3
    KALININGRAD = 4
    KRASNODAR = 5
    BASHKORTOSTAN = 6
    TATARSTAN = 7
    VOLGOGRAD = 8


class CurrencyStatistics(TypedDict):
    num_of_available_buys: int
    num_of_available_sells: int
    avg_buys: Optional[float]
    avg_sells: Optional[float]
    avg_price: Optional[float]
    min_spread_rub: float
    max_spread_rub: float
    avg_spread_rub: Optional[float]
