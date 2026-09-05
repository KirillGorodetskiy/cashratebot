from dataclasses import dataclass

from models import CurrencyCode


@dataclass(frozen=True)
class Currency:
    key: str
    rbc_id: int
    button: str


CURRENCIES: tuple[Currency, ...] = (
    Currency('USD', 3, '💵 USD'),
    Currency('EUR', 2, '💶 EUR'),
    Currency('GBP', 321, '💷 GBP'),
    Currency('AED', 5, '💴 AED'),
    Currency('CNY', 423, '💴 CNY'),
    Currency('CHF', 305, '₣ CHF'),
    Currency('TRY', 307, '₺ TRY'),
)


def currency_keys() -> frozenset[str]:
    return frozenset(item.key for item in CURRENCIES)


def get_rbc_id(code: str) -> int:
    key = code.upper()
    for item in CURRENCIES:
        if item.key == key:
            return item.rbc_id
    try:
        return CurrencyCode[key].value
    except KeyError as exc:
        raise ValueError(f'Unknown currency: {code}') from exc
