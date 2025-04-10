from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot_logic import get_quotes_df, get_statistics
from prompts import*
from db_manager import save_new_user_data_in_db, increment_field_db
from data_formatter import format_dataframe, format_stats_for_telegram
import os
from dotenv import load_dotenv

import logging

logger = logging.getLogger(__name__)

load_dotenv()

NUM_OF_RETURNED_BANKS = int(os.getenv("NUM_OF_RETURNED_BANKS"))

user_selection = {}  # Store user selections temporarily

currencies_list = ['usd', 'eur', 'gbp', 'aed']

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
            preapred_currency_data = format_dataframe(get_quotes_df(currency, city, NUM_OF_RETURNED_BANKS), user_lang) 
            if preapred_currency_data == "":
                message = prompt_messages_no_data[user_lang]
            else:
                message = prompt_messages_show_data[user_lang].format(currency=currency.upper(), city=cities_prompt[city.upper()][user_lang]) +\
                preapred_currency_data  # df is your DataFrame
                
            await query.message.reply_text(message[:4096])
            try:
                increment_field_db(user, 'filled_requests_currencies')
            except Exception as e:
                logger.error('Couldn`t increment filled_requests_currencies in db for user_id: %s'.format(user_id), e)

    elif data.startswith("get_statistics"):
        city = user_selection.get(user_id, {}).get("city", "Unknown")
        if (city == 'Unknown'):
            await query.message.reply_text(prompt_choose_city_first[user_lang])
        else:
            message = format_stats_for_telegram(get_statistics(city, currencies_list), user_lang)  
            await query.message.reply_text(message[:4096])
            try:
                increment_field_db(user, 'filled_requests_stats')
            except Exception as e:
                logger.error('Couldn`t increment filled_requests_stats in db for user_id: %s'.format(user_id), e) 
