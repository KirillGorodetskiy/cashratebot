import datetime
import html

import pandas as pd
import pytz


MSK = pytz.timezone('Europe/Moscow')
BANK_WIDTH = 16
CRUMB_CASH = {'en': 'Cash', 'ru': 'Наличные'}
CRUMB_STATS = {'en': 'Stats', 'ru': 'Статистика'}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _to_moscow(value: object) -> datetime.datetime:
    if hasattr(value, 'to_pydatetime'):
        value = value.to_pydatetime()
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            return MSK.localize(value)
        return value.astimezone(MSK)
    parsed = pd.to_datetime(value)
    if parsed.tzinfo is None:
        return MSK.localize(parsed.to_pydatetime())
    return parsed.tz_convert(MSK).to_pydatetime()


def card_header(
    crumbs: list[str],
    lang: str,
    updated_at: datetime.datetime | None = None,
) -> str:
    title = _esc(' · '.join(crumbs))
    when = updated_at if updated_at is not None else datetime.datetime.now(MSK)
    stamp = _to_moscow(when).strftime('%H:%M')
    if lang.lower() == 'ru':
        updated = f'<i>Обновлено {stamp} МСК</i>'
    else:
        updated = f'<i>Updated {stamp} MSK</i>'
    return f'<b>{title}</b>\n{updated}\n\n'


def _clip(name: str, width: int) -> str:
    if len(name) <= width:
        return name.ljust(width)
    return name[: width - 1] + '…'


def _fmt_rate(value: object) -> str:
    return f'{float(value):.2f}'


def format_dataframe(df: pd.DataFrame, lang: str) -> str:
    if df is None or df.empty:
        return ''

    is_ru = lang.lower() == 'ru'
    table_lines: list[str] = []
    extra_lines: list[str] = []

    for index, row in enumerate(df.itertuples(index=False), start=1):
        mark = '★' if index == 1 else ' '
        bank_raw = str(row.bank)
        buy = _fmt_rate(row.buy_quote)
        sell = _fmt_rate(row.sell_quote)
        spread_pct = _fmt_rate(row.spread_percent)
        table_lines.append(
            f'{mark}{index} {_clip(bank_raw, BANK_WIDTH)} '
            f'{buy:>6} {sell:>6} {spread_pct:>5}%'
        )

        shown_time = _esc(_to_moscow(row.time).strftime('%H:%M'))
        if is_ru:
            commission = 'Да' if row.commissions else 'Нет'
            extra_lines.append(
                f'{index}. {_esc(bank_raw)} · {shown_time} · '
                f'Комиссия: {commission}'
            )
        else:
            commission = 'Yes' if row.commissions else 'No'
            extra_lines.append(
                f'{index}. {_esc(bank_raw)} · {shown_time} · '
                f'Commission: {commission}'
            )

    table = _esc('\n'.join(table_lines))
    extra = '\n'.join(extra_lines)
    return (
        f'<pre>{table}</pre>\n'
        f'<blockquote expandable>{extra}</blockquote>'
    )


def format_stats_for_telegram(
    prepared_response: dict,
    lang: str = 'en',
) -> str:
    if not prepared_response:
        return ''

    is_ru = lang.lower() == 'ru'
    table_lines: list[str] = []
    extra_lines: list[str] = []

    for currency, stats in prepared_response.items():
        name = str(currency).upper()
        avg_buy = _fmt_rate(stats['avg_buys'] or 0)
        avg_sell = _fmt_rate(stats['avg_sells'] or 0)
        if stats['avg_buys'] is None:
            avg_buy = '—'
        if stats['avg_sells'] is None:
            avg_sell = '—'
        spread = stats['avg_spread_rub'] or '—'
        table_lines.append(
            f'{name:<4} {avg_buy:>6} / {avg_sell:<6}  ±{spread}'
        )

        avg_price = _esc(stats['avg_price'] or '—')
        min_spread = _esc(stats['min_spread_rub'] or '—')
        max_spread = _esc(stats['max_spread_rub'] or '—')
        buys = _esc(stats['num_of_available_buys'])
        sells = _esc(stats['num_of_available_sells'])
        shown = _esc(name)
        if is_ru:
            extra_lines.append(
                f'{shown}: средний {avg_price} · '
                f'спред {min_spread}–{max_spread} · '
                f'офферы {buys}/{sells}'
            )
        else:
            extra_lines.append(
                f'{shown}: avg {avg_price} · '
                f'spread {min_spread}–{max_spread} · '
                f'offers {buys}/{sells}'
            )

    table = _esc('\n'.join(table_lines))
    extra = '\n'.join(extra_lines)
    return (
        f'<pre>{table}</pre>\n'
        f'<blockquote expandable>{extra}</blockquote>'
    )
