import html
import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes

from bb_api import build_message, fetch_usdt_rub_rates
from bot_logic import get_quotes_df, get_statistics
from data_formatter import (
    CRUMB_CASH,
    CRUMB_STATS,
    card_header,
    format_dataframe,
    format_stats_for_telegram,
)
from db_manager import increment_field_db, save_new_user_data_in_db
from prompts import (
    cities_prompt,
    prompt_choose_city_first,
    prompt_help,
    prompt_messages_cities,
    prompt_messages_currencies,
    prompt_messages_error,
    prompt_messages_greeting,
    prompt_messages_no_data,
)
import ui

logger = logging.getLogger(__name__)

load_dotenv()

NUM_OF_RETURNED_BANKS = int(os.getenv('NUM_OF_RETURNED_BANKS', 5))
CURRENCIES_LIST = ['usd', 'eur', 'gbp', 'aed']


def _lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user = update.effective_user
    code = user.language_code if user is not None else None
    lang = ui.resolve_lang(code)
    context.user_data['lang'] = lang
    return lang


def _city_label(city: str, lang: str) -> str:
    return cities_prompt[city.upper()][lang]


async def _render(
    text: str,
    markup,
    query=None,
    message=None,
) -> None:
    if query is not None:
        try:
            await query.edit_message_text(
                text=text[:4096],
                reply_markup=markup,
                parse_mode=ParseMode.HTML,
            )
        except BadRequest as exc:
            if 'not modified' not in str(exc).lower():
                logger.error('Could not edit message: %s', exc)
                raise
        return
    if message is None:
        raise ValueError('query or message is required')
    await message.reply_text(
        text=text[:4096],
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )


async def _clear_reply_keyboard(message) -> None:
    notice = await message.reply_text(
        text='\u2060',
        reply_markup=ReplyKeyboardRemove(),
    )
    try:
        await notice.delete()
    except TelegramError as exc:
        logger.error(
            'Could not delete keyboard-clear notice: %s',
            exc,
        )


async def _show_home(
    context,
    lang: str,
    query=None,
    message=None,
    clear_reply_keyboard: bool = False,
) -> None:
    context.user_data['step'] = 'home'
    context.user_data.pop('mode', None)
    context.user_data.pop('city', None)
    context.user_data.pop('currency', None)
    if clear_reply_keyboard and message is not None:
        await _clear_reply_keyboard(message)
    await _render(
        prompt_messages_greeting[lang],
        ui.home_inline_keyboard(lang),
        query=query,
        message=message,
    )


async def _show_cities(context, lang: str, query=None, message=None) -> None:
    context.user_data['step'] = 'cities'
    context.user_data['mode'] = 'cash'
    await _render(
        prompt_messages_cities[lang],
        ui.cities_inline_keyboard(lang),
        query=query,
        message=message,
    )


async def _show_currencies(
    context,
    lang: str,
    city: str,
    query=None,
    message=None,
) -> None:
    context.user_data['step'] = 'currencies'
    context.user_data['city'] = city
    text = prompt_messages_currencies[lang].format(
        city=html.escape(_city_label(city, lang), quote=True),
        num_of_banks=NUM_OF_RETURNED_BANKS,
    )
    await _render(
        text,
        ui.currencies_inline_keyboard(lang),
        query=query,
        message=message,
    )


async def _show_quotes(
    context,
    lang: str,
    city: str,
    currency: str,
    user,
    count_request: bool,
    query=None,
    message=None,
) -> None:
    context.user_data['step'] = 'quotes'
    context.user_data['city'] = city
    context.user_data['currency'] = currency
    try:
        quotes_df = get_quotes_df(
            currency,
            city,
            NUM_OF_RETURNED_BANKS,
        )
        body = format_dataframe(quotes_df, lang)
    except Exception as exc:
        logger.error('Could not load quotes: %s', exc)
        body = ''
        text = prompt_messages_error[lang]
    else:
        if body == '':
            text = prompt_messages_no_data[lang]
        else:
            updated_at = None
            if quotes_df is not None and not quotes_df.empty:
                updated_at = quotes_df['time'].max()
            header = card_header(
                [
                    CRUMB_CASH[lang],
                    _city_label(city, lang),
                    currency.upper(),
                ],
                lang,
                updated_at,
            )
            text = header + body

    await _render(
        text,
        ui.result_inline_keyboard(lang),
        query=query,
        message=message,
    )
    if count_request:
        try:
            increment_field_db(user, 'filled_requests_currencies')
        except Exception as exc:
            logger.error(
                'Could not increment currency requests: %s',
                exc,
            )


async def _show_stats(
    context,
    lang: str,
    city: str,
    user,
    count_request: bool,
    query=None,
    message=None,
) -> None:
    context.user_data['step'] = 'stats'
    context.user_data['city'] = city
    try:
        stats = get_statistics(city, CURRENCIES_LIST)
        body = format_stats_for_telegram(stats, lang)
        if body == '':
            text = prompt_messages_no_data[lang]
        else:
            text = card_header(
                [
                    CRUMB_CASH[lang],
                    _city_label(city, lang),
                    CRUMB_STATS[lang],
                ],
                lang,
            ) + body
    except Exception as exc:
        logger.error('Could not load stats: %s', exc)
        text = prompt_messages_error[lang]

    await _render(
        text,
        ui.result_inline_keyboard(lang),
        query=query,
        message=message,
    )
    if count_request:
        try:
            increment_field_db(user, 'filled_requests_stats')
        except Exception as exc:
            logger.error('Could not increment stats requests: %s', exc)


async def _show_usdt(context, lang: str, query=None, message=None) -> None:
    context.user_data['step'] = 'usdt'
    context.user_data['mode'] = 'usdt'
    try:
        result = fetch_usdt_rub_rates()
        text = build_message(result, lang=lang)
    except Exception as exc:
        logger.error('Could not load USDT rates: %s', exc)
        text = prompt_messages_error[lang]
    await _render(
        text,
        ui.result_inline_keyboard(lang),
        query=query,
        message=message,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    save_new_user_data_in_db(user)
    lang = _lang(update, context)
    await _show_home(
        context,
        lang,
        message=update.message,
        clear_reply_keyboard=True,
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    lang = _lang(update, context)
    await update.message.reply_text(
        prompt_help[lang],
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove(),
    )


async def cash_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    lang = _lang(update, context)
    await _show_cities(context, lang, message=update.message)


async def usdt_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    lang = _lang(update, context)
    await _show_usdt(context, lang, message=update.message)


async def handle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return

    lang = _lang(update, context)
    user = update.effective_user
    data = query.data

    if data == 'nav:home':
        await query.answer(ui.TOAST_HOME[lang])
        await _show_home(context, lang, query=query)
        return

    if data == 'nav:back':
        await query.answer()
        await _go_back(context, lang, query)
        return

    if data == 'nav:refresh':
        await query.answer(ui.TOAST_REFRESH[lang])
        await _refresh(context, lang, user, query)
        return

    if data.startswith('mode:'):
        mode = ui.parse_mode(data)
        if mode is None:
            await query.answer(ui.TOAST_INVALID[lang])
            return
        await query.answer()
        if mode == 'cash':
            await _show_cities(context, lang, query=query)
            return
        await _show_usdt(context, lang, query=query)
        return

    if data.startswith('city:'):
        city = ui.parse_city(data)
        if city is None:
            await query.answer(ui.TOAST_INVALID[lang])
            return
        await query.answer(_city_label(city, lang))
        await _show_currencies(context, lang, city, query=query)
        return

    if data.startswith('currency:'):
        currency = ui.parse_currency(data)
        city = context.user_data.get('city')
        if currency is None:
            await query.answer(ui.TOAST_INVALID[lang])
            return
        if city not in ui.ALLOWED_CITIES:
            await query.answer(ui.TOAST_INVALID[lang])
            await _render(
                prompt_choose_city_first[lang],
                ui.cities_inline_keyboard(lang),
                query=query,
            )
            return
        await query.answer(currency)
        await _show_quotes(
            context,
            lang,
            city,
            currency,
            user,
            count_request=True,
            query=query,
        )
        return

    if data == 'stats':
        city = context.user_data.get('city')
        if city not in ui.ALLOWED_CITIES:
            await query.answer(ui.TOAST_INVALID[lang])
            await _render(
                prompt_choose_city_first[lang],
                ui.cities_inline_keyboard(lang),
                query=query,
            )
            return
        await query.answer()
        await _show_stats(
            context,
            lang,
            city,
            user,
            count_request=True,
            query=query,
        )
        return

    await query.answer(ui.TOAST_INVALID[lang])


async def _go_back(context, lang: str, query) -> None:
    step = context.user_data.get('step', 'home')
    target = ui.BACK_STEPS.get(step, 'home')
    city = context.user_data.get('city')
    if target == 'home':
        await _show_home(context, lang, query=query)
        return
    if target == 'cities':
        await _show_cities(context, lang, query=query)
        return
    if target == 'currencies' and city in ui.ALLOWED_CITIES:
        await _show_currencies(context, lang, city, query=query)
        return
    await _show_home(context, lang, query=query)


async def _refresh(context, lang: str, user, query) -> None:
    step = context.user_data.get('step')
    city = context.user_data.get('city')
    currency = context.user_data.get('currency')
    if step == 'usdt':
        await _show_usdt(context, lang, query=query)
        return
    if step == 'quotes' and city in ui.ALLOWED_CITIES and currency:
        await _show_quotes(
            context,
            lang,
            city,
            currency,
            user,
            count_request=False,
            query=query,
        )
        return
    if step == 'stats' and city in ui.ALLOWED_CITIES:
        await _show_stats(
            context,
            lang,
            city,
            user,
            count_request=False,
            query=query,
        )
        return
    await _show_home(context, lang, query=query)
