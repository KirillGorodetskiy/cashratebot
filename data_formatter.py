import html

import pandas as pd


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def format_dataframe(df: pd.DataFrame, lang: str) -> str:
    if df is None or df.empty:
        return ''

    rows: list[str] = []
    is_ru = lang.lower() == 'ru'

    for _, row in df.iterrows():
        time_str = row['time'].strftime('%H:%M')
        bank = _esc(row['bank'])
        buy = _esc(row['buy_quote'])
        sell = _esc(row['sell_quote'])
        spread = _esc(row['spread'])
        spread_pct = _esc(row['spread_percent'])
        shown_time = _esc(time_str)

        if is_ru:
            commission = 'Да' if row['commissions'] else 'Нет'
            rows.append(
                f'<b>{bank}</b>\n'
                f'Покупка <b>{buy}</b> · Продажа <b>{sell}</b>\n'
                f'Спред {spread} ₽ ({spread_pct}%) · '
                f'{shown_time} · Комиссия: {commission}'
            )
        else:
            commission = 'Yes' if row['commissions'] else 'No'
            rows.append(
                f'<b>{bank}</b>\n'
                f'Buy <b>{buy}</b> · Sell <b>{sell}</b>\n'
                f'Spread {spread} RUB ({spread_pct}%) · '
                f'{shown_time} · Commission: {commission}'
            )

    return '\n\n'.join(rows)


def format_stats_for_telegram(
    prepared_response: dict,
    lang: str = 'en',
) -> str:
    if not prepared_response:
        return ''

    is_ru = lang.lower() == 'ru'
    parts: list[str] = []

    for currency, stats in prepared_response.items():
        name = _esc(str(currency).upper())
        avg_buy = _esc(stats['avg_buys'] or '—')
        avg_sell = _esc(stats['avg_sells'] or '—')
        avg_price = _esc(stats['avg_price'] or '—')
        avg_spread = _esc(stats['avg_spread_rub'] or '—')
        min_spread = _esc(stats['min_spread_rub'] or '—')
        max_spread = _esc(stats['max_spread_rub'] or '—')
        buys = _esc(stats['num_of_available_buys'])
        sells = _esc(stats['num_of_available_sells'])

        if is_ru:
            parts.append(
                f'<b>{name}</b>\n'
                f'Средняя покупка <b>{avg_buy}</b> · '
                f'продажа <b>{avg_sell}</b>\n'
                f'Средний курс {avg_price}\n'
                f'Спред {avg_spread} ₽ '
                f'(мин. {min_spread} · макс. {max_spread})\n'
                f'Офферы: купить {buys} · продать {sells}'
            )
        else:
            parts.append(
                f'<b>{name}</b>\n'
                f'Avg buy <b>{avg_buy}</b> · '
                f'sell <b>{avg_sell}</b>\n'
                f'Avg price {avg_price}\n'
                f'Spread {avg_spread} RUB '
                f'(min {min_spread} · max {max_spread})\n'
                f'Offers: buy {buys} · sell {sells}'
            )

    return '\n\n'.join(parts)
