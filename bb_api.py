import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Trusted seller criteria from .env
TRUSTED_MIN_ORDERS = int(os.getenv("TRUSTED_MIN_ORDERS", "1000"))
TRUSTED_MIN_SUCCESS = float(os.getenv("TRUSTED_MIN_SUCCESS", "95"))

def fetch_bybit_p2p_stats(side="buy"):
    url = "https://api2.bybit.com/fiat/otc/item/online"
    
    # Side: 1 = BUY (you buy USDT), 0 = SELL (you sell USDT)
    side_code = "1" if side == "buy" else "0"
    
    payload = {
        "tokenId": "USDT",
        "currencyId": "RUB",
        "side": side_code,
        "size": "10000"
    }
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://www.bybit.com",
        "Referer": "https://www.bybit.com/",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        ads = response.json().get("result", {}).get("items", [])
        df = pd.DataFrame(ads)

        df['price'] = df['price'].astype(float)
        df['minAmount'] = df['minAmount'].astype(float)
        df['maxAmount'] = df['maxAmount'].astype(float)
        df['orderNum'] = df['orderNum'].astype(float)
        df['finishNum'] = df['finishNum'].astype(float)
        df['successRate'] = (df['finishNum'] / df['orderNum']) * 100
        df['successRate'] = df['successRate'].fillna(0)

        stats = {
            "price_min": df['price'].min(),
            "price_max": df['price'].max(),
            "price_mean": df['price'].mean(),
            "price_median": df['price'].median(),
            "min_amount_mean": df['minAmount'].mean(),
            "min_amount_median": df['minAmount'].median(),
            "max_amount_mean": df['maxAmount'].mean(),
            "max_amount_median": df['maxAmount'].median(),
            "mean_success_rate": df['successRate'].mean(),
            "side": side,
            "good_sellers": {
                "count_100_trades": int((df['orderNum'] >= 100).sum()),
                "count_95_percent_success": int((df['successRate'] >= 95).sum())
            }
        }

        trusted = df[(df['orderNum'] >= TRUSTED_MIN_ORDERS) & (df['successRate'] >= TRUSTED_MIN_SUCCESS)]

        target_amounts = [10000, 30000, 60000, 100000]
        avg_prices_by_amount = {}
        for amount in target_amounts:
            eligible = trusted[(trusted['minAmount'] <= amount) & (trusted['maxAmount'] >= amount)]
            avg_price = eligible['price'].mean() if not eligible.empty else None
            avg_prices_by_amount[amount] = avg_price

        stats["trusted"] = {
            "count": len(trusted),
            "price_mean": trusted['price'].mean(),
            "price_median": trusted['price'].median(),
            "success_mean": trusted['successRate'].mean(),
            "min_avg": trusted['minAmount'].mean(),
            "max_avg": trusted['maxAmount'].mean(),
            "avg_prices_by_amount": avg_prices_by_amount
        }

        return stats

    except Exception as e:
        print("❌ Error fetching data:", e)
        return None

def build_telegram_message(stats: dict, lang: str = "en") -> str:
    if not stats:
        return "❌ Failed to fetch market stats." if lang == "en" else "❌ Не удалось получить данные с рынка."

    side_label = "Buy" if stats["side"] == "buy" else "Sell"
    side_label_ru = "Покупка" if stats["side"] == "buy" else "Продажа"

    amounts_section = "\n".join([
        f"  • {amount:>6,} RUB: {stats['trusted']['avg_prices_by_amount'][amount]:.2f} RUB"
        if stats['trusted']['avg_prices_by_amount'][amount] is not None
        else f"  • {amount:>6,} RUB: —"
        for amount in stats['trusted']['avg_prices_by_amount']
    ])

    if lang == "ru":
        return f"""
💸 Сводка (USDT {side_label_ru}): 
• Цена: {stats["price_min"]:.2f} – {stats["price_max"]:.2f} RUB
• Медиана: {stats["price_median"]:.2f} | Средняя: {stats["price_mean"]:.2f}

📊 Лимиты объявлений:
• Мин. сумма — Средняя: {stats["min_amount_mean"]:,.0f} | Медиана: {stats["min_amount_median"]:,.0f} RUB
• Макс. сумма — Средняя: {stats["max_amount_mean"]:,.0f} | Медиана: {stats["max_amount_median"]:,.0f} RUB

🧑‍💼 Статистика продавцов:
• Ср. уровень успешных сделок: {stats["mean_success_rate"]:.1f}%
• Продавцов с 100+ сделок: {stats["good_sellers"]["count_100_trades"]}
• Продавцов с 95%+ успеха: {stats["good_sellers"]["count_95_percent_success"]}

🏅 Статичтика надежных продавцов ({TRUSTED_MIN_ORDERS}+ сделок, {TRUSTED_MIN_SUCCESS}%+ успеха):
• Кол-во: {stats["trusted"]["count"]}
• Ср. успех: {stats["trusted"]["success_mean"]:.1f}%
• Ср. цена: {stats["trusted"]["price_mean"]:.2f} | Медиана: {stats["trusted"]["price_median"]:.2f}
• Ср. мин.: {stats["trusted"]["min_avg"]:,.0f} | Ср. макс.: {stats["trusted"]["max_avg"]:,.0f} RUB
• Средняя цена по суммам:
{amounts_section}
""".strip()
    
    # English version
    return f"""
💸 USDT {side_label} Stats:
• Price: {stats["price_min"]:.2f} – {stats["price_max"]:.2f} RUB
• Median: {stats["price_median"]:.2f} | Mean: {stats["price_mean"]:.2f}

📊 Ad Limits:
• Min amount — Avg: {stats["min_amount_mean"]:,.0f} | Median: {stats["min_amount_median"]:,.0f} RUB
• Max amount — Avg: {stats["max_amount_mean"]:,.0f} | Median: {stats["max_amount_median"]:,.0f} RUB

🧑‍💼 Seller Reliability:
• Avg success rate: {stats["mean_success_rate"]:.1f}%
• Sellers with 100+ trades: {stats["good_sellers"]["count_100_trades"]}
• Sellers with 95%+ success: {stats["good_sellers"]["count_95_percent_success"]}

🏅 Trusted Sellers ({TRUSTED_MIN_ORDERS}+ trades, {TRUSTED_MIN_SUCCESS}%+ success):
• Count: {stats["trusted"]["count"]}
• Avg success rate: {stats["trusted"]["success_mean"]:.1f}%
• Avg price: {stats["trusted"]["price_mean"]:.2f} RUB | Median: {stats["trusted"]["price_median"]:.2f}
• Avg min.: {stats["trusted"]["min_avg"]:,.0f} | Avg max.: {stats["trusted"]["max_avg"]:,.0f} RUB
• Avg prices by amount:
{amounts_section}
""".strip()

# Example usage
if __name__ == "__main__":
    stats = fetch_bybit_p2p_stats(side="buy")  # or "sell"
    message_en = build_telegram_message(stats, lang="en")
    message_ru = build_telegram_message(stats, lang="ru")
    print(message_en)
    print("\n" + "-"*80 + "\n")
    print(message_ru)
