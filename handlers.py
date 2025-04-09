from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core_logic import get_quotes, get_statistics
import pandas as pd
from prompts import*
from db_manager import save_new_user_data_in_db, increment_field_db

import os
from dotenv import load_dotenv

import logging

logger = logging.getLogger(__name__)

load_dotenv()

NUM_OF_RETURNED_BANKS=int(os.getenv("NUM_OF_RETURNED_BANKS"))

user_selection = {}  # Store user selections temporarily

currencies_list = ['usd', 'eur', 'gbp', 'aed']

# Sample: format your DataFrame into a readable string
def format_dataframe(df: pd.DataFrame, lang: str) -> str:
    rows = []

    for _, row in df.iterrows():
        time_str = row['time'].strftime("%H:%M")
        commission_str = "Yes" if row['comissions'] else "No"
        if lang.lower() == 'ru':
            commission_str = "Да" if row['comissions'] else "Нет"

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

keyboards_cities = { 'en' : [
        [InlineKeyboardButton("🏙️ Moscow", callback_data="city:Moscow")],
        [InlineKeyboardButton("🏰 St. Petersburg", callback_data="city:SPB")]
    ],
    'ru' : [
        [InlineKeyboardButton("🏙️ Москва", callback_data="city:Moscow")],
        [InlineKeyboardButton("🏰 Санкт-Петербург", callback_data="city:SPB")]
    ]    
}
    
# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    save_new_user_data_in_db(user)

    user_id = user.id

    user_lang = update.effective_user.language_code
    user_selection[user_id] = {"user_lang": user_lang}

    keyboard = keyboards_cities[user_lang]
    await update.message.reply_text(prompt_messages_greeting[user_lang] + prompt_messages_cities[user_lang], reply_markup=InlineKeyboardMarkup(keyboard))

# Step 2: Ask for currency after city is chosen
async def handle_callback(update, context):

    user = update.effective_user

    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_lang = query.from_user.language_code
    
    data = query.data
    if data.startswith("city:"):
        city = data.split(":")[1]
        user_selection[user_id] = {"city": city}

        keyboard = [
            [InlineKeyboardButton("💵 USD", callback_data="currency:USD"),
             InlineKeyboardButton("💶 EUR", callback_data="currency:EUR"),
             InlineKeyboardButton("💷 GBP", callback_data="currency:GBP"),
             InlineKeyboardButton("💴 AED", callback_data="currency:AED")
            ],
            [
            InlineKeyboardButton(prompt_get_statistics[user_lang], callback_data="get_statistics")
            ]
        ]
        await query.message.reply_text(prompt_messages_currencies[user_lang]\
                                       .format(city=cities_prompt[city.upper()][user_lang], num_of_banks=NUM_OF_RETURNED_BANKS),\
                                        reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("currency:"):
        currency = data.split(":")[1]
        city = user_selection.get(user_id, {}).get("city", "Unknown")
        if (city == 'Unknown'):
            await query.message.reply_text(prompt_choose_city_first[user_lang])
        else:
            await query.message.reply_text(prompt_messages_choiced[user_lang].format(city=cities_prompt[city.upper()][user_lang], currency=currency))
            preapred_currency_data = format_dataframe(get_quotes(currency, city, NUM_OF_RETURNED_BANKS), user_lang) 
            if preapred_currency_data == "":
                message = prompt_messages_no_data[user_lang]
            else:
                message = prompt_messages_show_data[user_lang].format(currency=currency.upper(), city=cities_prompt[city.upper()][user_lang]) +\
                preapred_currency_data  # df is your DataFrame
                
            await query.message.reply_text(message[:4096])

            increment_field_db(user, 'filled_requests_currencies')

    elif data.startswith("get_statistics"):
        city = user_selection.get(user_id, {}).get("city", "Unknown")
        if (city == 'Unknown'):
            await query.message.reply_text(prompt_choose_city_first[user_lang])
        else:
            message = format_stats_for_telegram(get_statistics(city, currencies_list), user_lang)  
            await query.message.reply_text(message[:4096])

            increment_field_db(user, 'filled_requests_stats')
