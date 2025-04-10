from dataclasses import dataclass
import datetime


@dataclass
class QuotesData:
    banks_names: list[str]
    quotes: list[float]
    times: list[datetime.datetime]
    commissions: list[bool]
    currency: list[str]