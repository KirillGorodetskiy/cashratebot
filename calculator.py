import html
import re


MAX_AMOUNT = 1_000_000_000


def parse_amount(text: str) -> float | None:
    cleaned = text.strip().replace(' ', '').replace(',', '.')
    if not re.fullmatch(r'\d+(\.\d{1,4})?', cleaned):
        return None
    value = float(cleaned)
    if value <= 0 or value > MAX_AMOUNT:
        return None
    return value


def convert_amount(
    amount: float,
    buy: float,
    sell: float,
) -> dict[str, float]:
    return {
        'pay_rub': round(amount * float(buy), 2),
        'get_rub': round(amount * float(sell), 2),
    }


def format_conversion(
    amount: float,
    currency: str,
    bank: str,
    result: dict[str, float],
    lang: str,
) -> str:
    shown_ccy = html.escape(currency, quote=True)
    shown_bank = html.escape(bank, quote=True)
    if lang == 'ru':
        return (
            f'<b>{amount:g} {shown_ccy}</b> · {shown_bank}\n'
            f'Купить: {result["pay_rub"]:,.2f} ₽\n'
            f'Продать: {result["get_rub"]:,.2f} ₽'
        )
    return (
        f'<b>{amount:g} {shown_ccy}</b> · {shown_bank}\n'
        f'Buy: {result["pay_rub"]:,.2f} RUB\n'
        f'Sell: {result["get_rub"]:,.2f} RUB'
    )
