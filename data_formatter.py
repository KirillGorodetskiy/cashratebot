import pandas as pd

# Sample: format your DataFrame into a readable string
def format_dataframe(df: pd.DataFrame, lang: str) -> str:
    rows = []

    for _, row in df.iterrows():
        time_str = row['time'].strftime("%H:%M")
        commission_str = "Yes" if row['commissions'] else "No"
        if lang.lower() == 'ru':
            commission_str = "Да" if row['commissions'] else "Нет"

        if lang.lower() == 'en':
            row_text = (
                f"🏦 {row['bank']}\n"
                f"💵 Buy: {row['buy_quote']}\n"
                f"💴 Sell: {row['sell_quote']}\n"
                f"📊 Avg price: {row['avg_price']}\n"
                f"📉 Spread, RUB: {row['spread']}\n"
                f"📈 Spread, %: {row['spread_percent']}%\n"
                f"📅 Time: {time_str}\n"
                f"💸 Additional Commission: {commission_str}"
            )
        else:
            row_text = (
                f"🏦 {row['bank']}\n"
                f"💵 Покупка: {row['buy_quote']}\n"
                f"💴 Продажа: {row['sell_quote']}\n"
                f"📊 Средняя цена: {row['avg_price']}\n"
                f"📉 Спрэд (₽): {row['spread']}\n"
                f"📈 Спрэд (%): {row['spread_percent']}%\n"
                f"📅 Время: {time_str}\n"
                f"💸 Доп. комиссия: {commission_str}"
            )

        rows.append(row_text)

    return "\n\n".join(rows)  # Add double newline to separate rows
    

def format_stats_for_telegram(prepared_response: dict, lang: str = "en") -> str:
    message_parts = []

    for currency, stats in prepared_response.items():
        if lang.lower() == "ru":
            part = (
                f"💱 Валюта: {currency.upper()}\n"
                f"📊 Средний курс покупки: {stats['avg_buys'] or '—'}\n"
                f"📈 Средний курс продажи: {stats['avg_sells'] or '—'}\n"
                f"⚖️ Средний курс: {stats['avg_price'] or '—'}\n"
                f"📉 Средний спред: {stats['avg_spread_rub'] or '—'} руб.\n"
                f"🔽 Мин. спред: {stats['min_spread_rub'] or '—'} руб.\n"
                f"🔼 Макс. спред: {stats['max_spread_rub'] or '—'} руб.\n"
                f"🧾 Кол-во предложений Купить: {stats['num_of_available_buys']} | Продать: {stats['num_of_available_sells']}\n"
            )
        else:
            part = (
                f"💱 Currency: {currency.upper()}\n"
                f"📊 Avg Buy: {stats['avg_buys'] or '—'}\n"
                f"📈 Avg Sell: {stats['avg_sells'] or '—'}\n"
                f"⚖️ Avg Price: {stats['avg_price'] or '—'}\n"
                f"📉 Avg Spread: {stats['avg_spread_rub'] or '—'} RUB\n"
                f"🔽 Min Spread: {stats['min_spread_rub'] or '—'} RUB\n"
                f"🔼 Max Spread: {stats['max_spread_rub'] or '—'} RUB\n"
                f"🧾 Buy Offers: {stats['num_of_available_buys']} | Sell Offers: {stats['num_of_available_sells']}\n"
            )

        message_parts.append(part)

    return "\n\n".join(message_parts)