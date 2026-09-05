import html
import logging
import os
import uuid

from dotenv import load_dotenv
from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes

from bb_api import build_message, fetch_usdt_rub_rates
from bot_logic import get_quotes_df, get_statistics
from calculator import convert_amount, format_conversion, parse_amount
from cbr_rates import cbr_compare_line
from currencies import CURRENCIES
from data_formatter import (
    CRUMB_CASH,
    CRUMB_STATS,
    card_header,
    format_dataframe,
    format_stats_for_telegram,
)
from db_manager import (
    create_alert,
    delete_alert,
    get_user_prefs,
    increment_field_db,
    list_alerts,
    mark_alert_triggered,
    save_new_user_data_in_db,
    set_favorite,
    set_last_lookup,
)
from history_store import load_history, summarize_history
from inline_search import parse_inline_query
from jobs import evaluate_alerts
from office_info import fetch_bank_info, format_office
from prompts import (
    cities_prompt,
    prompt_alert,
    prompt_alert_th,
    prompt_alerts_empty,
    prompt_alerts_list,
    prompt_calc,
    prompt_choose_city_first,
    prompt_help,
    prompt_inline_hint,
    prompt_messages_cities,
    prompt_messages_currencies,
    prompt_messages_error,
    prompt_messages_greeting,
    prompt_messages_no_data,
    prompt_no_offices,
    prompt_offices,
)
import ui

logger = logging.getLogger(__name__)

load_dotenv()

NUM_OF_RETURNED_BANKS = int(os.getenv('NUM_OF_RETURNED_BANKS', 5))
CURRENCIES_LIST = [item.key.lower() for item in CURRENCIES]


def _lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user = update.effective_user
    code = user.language_code if user is not None else None
    lang = ui.resolve_lang(code)
    context.user_data['lang'] = lang
    return lang


def _city_label(city: str, lang: str) -> str:
    return cities_prompt[city.upper()][lang]


def _valid_pair(city: object, currency: object) -> bool:
    return (
        city in ui.ALLOWED_CITIES
        and currency in ui.ALLOWED_CURRENCIES
    )


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
    user=None,
) -> None:
    context.user_data['step'] = 'home'
    context.user_data.pop('mode', None)
    context.user_data.pop('city', None)
    context.user_data.pop('currency', None)
    prefs = _empty_prefs()
    if user is not None:
        try:
            prefs = get_user_prefs(user.id)
        except Exception as exc:
            logger.error('Could not load prefs: %s', exc)
    if clear_reply_keyboard and message is not None:
        await _clear_reply_keyboard(message)
    await _render(
        prompt_messages_greeting[lang],
        ui.home_inline_keyboard(lang, prefs),
        query=query,
        message=message,
    )


def _empty_prefs() -> dict:
    return {
        'last_city': None,
        'last_currency': None,
        'fav_city': None,
        'fav_currency': None,
    }


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


def _quote_extras(city: str, currency: str, quotes_df, lang: str) -> str:
    lines: list[str] = []
    if quotes_df is not None and not quotes_df.empty:
        try:
            best = float(quotes_df.iloc[0]['buy_quote'])
        except (TypeError, ValueError, KeyError):
            best = None
        if best:
            cbr = cbr_compare_line(currency, best, lang)
            if cbr:
                lines.append(f'<i>{html.escape(cbr)}</i>')
    hist = summarize_history(load_history(city, currency), lang)
    if hist:
        lines.append(f'<code>{html.escape(hist)}</code>')
    if not lines:
        return ''
    return '\n'.join(lines) + '\n\n'


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
    context.user_data['mode'] = 'cash'
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
        quotes_df = None
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
            extras = _quote_extras(city, currency, quotes_df, lang)
            text = header + extras + body

    await _render(
        text,
        ui.result_inline_keyboard(lang, 'quotes'),
        query=query,
        message=message,
    )
    if user is not None:
        try:
            set_last_lookup(user.id, city, currency)
        except Exception as exc:
            logger.error('Could not save last lookup: %s', exc)
        if quotes_df is not None and not quotes_df.empty:
            try:
                rate = float(quotes_df.iloc[0]['buy_quote'])
                await _notify_pair_alerts(
                    context, user, city, currency, rate, lang,
                )
            except Exception as exc:
                logger.error('Could not check alerts: %s', exc)
    if count_request:
        try:
            increment_field_db(user, 'filled_requests_currencies')
        except Exception as exc:
            logger.error(
                'Could not increment currency requests: %s',
                exc,
            )


async def _notify_pair_alerts(
    context,
    user,
    city: str,
    currency: str,
    rate: float,
    lang: str,
) -> None:
    alerts = []
    for item in list_alerts(user.id):
        if item['kind'] != 'cash_buy':
            continue
        if item['city'] != city or item['currency'] != currency:
            continue
        item['user_id'] = user.id
        item['lang'] = lang
        alerts.append(item)
    due = evaluate_alerts(alerts, lambda _alert: rate)
    for item in due:
        await context.bot.send_message(
            chat_id=item['user_id'],
            text=item['text'],
        )
        mark_alert_triggered(item['id'])


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
        ui.result_inline_keyboard(lang, 'stats'),
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
        result = None
    await _render(
        text,
        ui.result_inline_keyboard(lang, 'usdt'),
        query=query,
        message=message,
    )
    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    save_new_user_data_in_db(user)
    lang = _lang(update, context)
    await _show_home(
        context,
        lang,
        message=update.message,
        clear_reply_keyboard=True,
        user=user,
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
        await _show_home(context, lang, query=query, user=user)
        return

    if data == 'nav:back':
        await query.answer()
        await _go_back(context, lang, user, query)
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

    if data in {'last:open', 'fav:open'}:
        await _open_saved_pair(context, lang, user, query, data)
        return

    if data == 'fav:set':
        await _save_favorite(context, lang, user, query)
        return

    if data == 'calc:open':
        await _open_calc(context, lang, query)
        return

    if data.startswith('calc:'):
        amount = ui.parse_calc_preset(data)
        if amount is None:
            await query.answer(ui.TOAST_INVALID[lang])
            return
        await query.answer()
        await _show_conversion(
            context, lang, amount, query=query,
        )
        return

    if data == 'alert:open':
        await _open_alert(context, lang, query)
        return

    if data.startswith('alert:dir:'):
        direction = ui.parse_alert_dir(data)
        if direction is None:
            await query.answer(ui.TOAST_INVALID[lang])
            return
        await query.answer()
        await _open_alert_thresholds(
            context, lang, direction, query,
        )
        return

    if data.startswith('alert:th:'):
        threshold = ui.parse_threshold(data)
        if threshold is None:
            await query.answer(ui.TOAST_INVALID[lang])
            return
        await _create_alert(context, lang, user, threshold, query)
        return

    if data == 'alerts:list':
        await query.answer()
        await _show_alerts(context, lang, user, query=query)
        return

    if data.startswith('alert:del:'):
        alert_id = ui.parse_alert_id(data)
        if alert_id is None:
            await query.answer(ui.TOAST_INVALID[lang])
            return
        delete_alert(user.id, alert_id)
        await query.answer(ui.TOAST_SAVED[lang])
        await _show_alerts(context, lang, user, query=query)
        return

    if data == 'where:open':
        await query.answer()
        await _open_offices(context, lang, query)
        return

    if data.startswith('office:'):
        bank_id = ui.parse_office_id(data)
        if bank_id is None:
            await query.answer(ui.TOAST_INVALID[lang])
            return
        await query.answer()
        await _show_office(context, lang, bank_id, query)
        return

    await query.answer(ui.TOAST_INVALID[lang])


async def _open_saved_pair(context, lang, user, query, data: str) -> None:
    prefs = get_user_prefs(user.id)
    if data == 'last:open':
        city = prefs.get('last_city')
        currency = prefs.get('last_currency')
    else:
        city = prefs.get('fav_city')
        currency = prefs.get('fav_currency')
    if not _valid_pair(city, currency):
        await query.answer(ui.TOAST_INVALID[lang])
        return
    await query.answer(f'{city} {currency}')
    await _show_quotes(
        context,
        lang,
        city,
        currency,
        user,
        count_request=True,
        query=query,
    )


async def _save_favorite(context, lang, user, query) -> None:
    city = context.user_data.get('city')
    currency = context.user_data.get('currency')
    if not _valid_pair(city, currency):
        await query.answer(ui.TOAST_INVALID[lang])
        return
    set_favorite(user.id, city, currency)
    await query.answer(ui.TOAST_SAVED[lang])


async def _open_calc(context, lang, query) -> None:
    city = context.user_data.get('city')
    currency = context.user_data.get('currency')
    if not _valid_pair(city, currency):
        await query.answer(ui.TOAST_INVALID[lang])
        return
    context.user_data['step'] = 'calc_wait'
    await query.answer()
    await _render(
        prompt_calc[lang],
        ui.calc_inline_keyboard(lang),
        query=query,
    )


async def _show_conversion(
    context,
    lang: str,
    amount: float,
    query=None,
    message=None,
) -> None:
    city = context.user_data.get('city')
    currency = context.user_data.get('currency')
    if not _valid_pair(city, currency):
        text = prompt_choose_city_first[lang]
        await _render(
            text, ui.cities_inline_keyboard(lang),
            query=query, message=message,
        )
        return
    context.user_data['step'] = 'calc'
    try:
        quotes_df = get_quotes_df(currency, city, 1)
        if quotes_df is None or quotes_df.empty:
            text = prompt_messages_no_data[lang]
        else:
            row = quotes_df.iloc[0]
            result = convert_amount(
                amount,
                float(row['buy_quote']),
                float(row['sell_quote']),
            )
            text = format_conversion(
                amount,
                currency,
                str(row['bank']),
                result,
                lang,
            )
    except Exception as exc:
        logger.error('Could not convert amount: %s', exc)
        text = prompt_messages_error[lang]
    await _render(
        text,
        ui.calc_inline_keyboard(lang),
        query=query,
        message=message,
    )


async def _open_alert(context, lang, query) -> None:
    step = context.user_data.get('step')
    if step == 'usdt':
        context.user_data['alert_kind'] = 'usdt'
    elif _valid_pair(
        context.user_data.get('city'),
        context.user_data.get('currency'),
    ):
        context.user_data['alert_kind'] = 'cash_buy'
    else:
        await query.answer(ui.TOAST_INVALID[lang])
        return
    context.user_data['alert_from'] = step
    context.user_data['step'] = 'alert'
    await query.answer()
    await _render(
        prompt_alert[lang],
        ui.alert_dir_keyboard(lang),
        query=query,
    )


async def _current_alert_rate(context) -> float | None:
    kind = context.user_data.get('alert_kind')
    if kind == 'usdt':
        result = fetch_usdt_rub_rates()
        if not result:
            return None
        return float(result['median'])
    city = context.user_data.get('city')
    currency = context.user_data.get('currency')
    if not _valid_pair(city, currency):
        return None
    quotes_df = get_quotes_df(currency, city, 1)
    if quotes_df is None or quotes_df.empty:
        return None
    return float(quotes_df.iloc[0]['buy_quote'])


async def _open_alert_thresholds(context, lang, direction, query) -> None:
    try:
        rate = await _current_alert_rate(context)
    except Exception as exc:
        logger.error('Could not load alert rate: %s', exc)
        rate = None
    if rate is None:
        await query.answer(ui.TOAST_INVALID[lang])
        return
    context.user_data['alert_dir'] = direction
    context.user_data['step'] = 'alert'
    await _render(
        prompt_alert_th[lang].format(rate=rate),
        ui.alert_threshold_keyboard(rate, lang),
        query=query,
    )


async def _create_alert(context, lang, user, threshold, query) -> None:
    kind = context.user_data.get('alert_kind')
    direction = context.user_data.get('alert_dir')
    if kind not in {'cash_buy', 'usdt'}:
        await query.answer(ui.TOAST_INVALID[lang])
        return
    if direction not in ui.ALLOWED_ALERT_DIRS:
        await query.answer(ui.TOAST_INVALID[lang])
        return
    city = context.user_data.get('city')
    currency = context.user_data.get('currency')
    if kind == 'usdt':
        city = None
        currency = 'USDT'
    elif not _valid_pair(city, currency):
        await query.answer(ui.TOAST_INVALID[lang])
        return
    try:
        created = create_alert(
            user.id, kind, city, currency, direction, threshold,
        )
    except ValueError:
        await query.answer(ui.TOAST_INVALID[lang])
        return
    if not created:
        await query.answer(ui.TOAST_ALERT_LIMIT[lang])
        return
    await query.answer(ui.TOAST_ALERT[lang])
    await _show_alerts(context, lang, user, query=query)


async def _show_alerts(context, lang, user, query=None, message=None) -> None:
    context.user_data['step'] = 'alerts'
    alerts = list_alerts(user.id)
    if not alerts:
        text = prompt_alerts_empty[lang]
    else:
        text = prompt_alerts_list[lang]
    await _render(
        text,
        ui.alerts_list_keyboard(alerts, lang),
        query=query,
        message=message,
    )


async def _open_offices(context, lang, query) -> None:
    city = context.user_data.get('city')
    currency = context.user_data.get('currency')
    if not _valid_pair(city, currency):
        await query.answer(ui.TOAST_INVALID[lang])
        return
    try:
        quotes_df = get_quotes_df(
            currency, city, NUM_OF_RETURNED_BANKS,
        )
    except Exception as exc:
        logger.error('Could not load offices: %s', exc)
        await _render(
            prompt_messages_error[lang],
            ui.result_inline_keyboard(lang, 'quotes'),
            query=query,
        )
        return
    offices: list[tuple[str, str]] = []
    if quotes_df is not None and not quotes_df.empty:
        if 'bank_id' in quotes_df.columns:
            for row in quotes_df.itertuples(index=False):
                bank_id = str(getattr(row, 'bank_id', '') or '')
                if ui.parse_office_id(f'office:{bank_id}') is None:
                    continue
                offices.append((bank_id, str(row.bank)))
    if not offices:
        await _render(
            prompt_no_offices[lang],
            ui.result_inline_keyboard(lang, 'quotes'),
            query=query,
        )
        return
    context.user_data['step'] = 'offices'
    await _render(
        prompt_offices[lang],
        ui.offices_keyboard(offices, lang),
        query=query,
    )


async def _show_office(context, lang, bank_id: str, query) -> None:
    context.user_data['step'] = 'office'
    info = fetch_bank_info(bank_id)
    if info is None:
        text = prompt_messages_error[lang]
    else:
        text = format_office(info, lang)
    await _render(
        text,
        ui.nav_inline_keyboard(lang),
        query=query,
    )


async def _go_back(context, lang: str, user, query) -> None:
    step = context.user_data.get('step', 'home')
    target = ui.BACK_STEPS.get(step, 'home')
    city = context.user_data.get('city')
    currency = context.user_data.get('currency')
    if step == 'alert' and context.user_data.get('alert_from') == 'usdt':
        await _show_usdt(context, lang, query=query)
        return
    if target == 'home':
        await _show_home(context, lang, query=query, user=user)
        return
    if target == 'cities':
        await _show_cities(context, lang, query=query)
        return
    if target == 'currencies' and city in ui.ALLOWED_CITIES:
        await _show_currencies(context, lang, city, query=query)
        return
    if target == 'quotes' and _valid_pair(city, currency):
        await _show_quotes(
            context, lang, city, currency, user,
            count_request=False, query=query,
        )
        return
    if target == 'offices':
        await _open_offices(context, lang, query)
        return
    await _show_home(context, lang, query=query, user=user)


async def _refresh(context, lang: str, user, query) -> None:
    step = context.user_data.get('step')
    city = context.user_data.get('city')
    currency = context.user_data.get('currency')
    if step == 'usdt':
        await _show_usdt(context, lang, query=query)
        return
    if step == 'quotes' and _valid_pair(city, currency):
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
    await _show_home(context, lang, query=query, user=user)


async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if context.user_data.get('step') != 'calc_wait':
        return
    if update.message is None or update.message.text is None:
        return
    lang = _lang(update, context)
    amount = parse_amount(update.message.text)
    if amount is None:
        await update.message.reply_text(
            prompt_calc[lang],
            parse_mode=ParseMode.HTML,
            reply_markup=ui.calc_inline_keyboard(lang),
        )
        return
    await _show_conversion(
        context, lang, amount, message=update.message,
    )


def _inline_cash_text(city: str, currency: str, lang: str) -> str:
    quotes_df = get_quotes_df(currency, city, NUM_OF_RETURNED_BANKS)
    body = format_dataframe(quotes_df, lang)
    if body == '':
        return prompt_messages_no_data[lang]
    updated_at = quotes_df['time'].max()
    header = card_header(
        [CRUMB_CASH[lang], _city_label(city, lang), currency],
        lang,
        updated_at,
    )
    extras = _quote_extras(city, currency, quotes_df, lang)
    return header + extras + body


async def handle_inline(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.inline_query
    if query is None:
        return
    lang = ui.resolve_lang(
        query.from_user.language_code if query.from_user else None
    )
    parsed = parse_inline_query(query.query)
    if parsed is None:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=prompt_inline_hint[lang],
                input_message_content=InputTextMessageContent(
                    prompt_inline_hint[lang],
                ),
            )
        ]
        await query.answer(results, cache_time=10)
        return
    try:
        if parsed['kind'] == 'usdt':
            result = fetch_usdt_rub_rates()
            text = build_message(result, lang=lang)
            title = 'USDT / RUB'
        else:
            text = _inline_cash_text(
                parsed['city'], parsed['currency'], lang,
            )
            title = f'{parsed["city"]} {parsed["currency"]}'
    except Exception as exc:
        logger.error('Inline query failed: %s', exc)
        text = prompt_messages_error[lang]
        title = 'Error'
    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=title,
            input_message_content=InputTextMessageContent(
                text[:4096],
                parse_mode=ParseMode.HTML,
            ),
        )
    ]
    await query.answer(results, cache_time=30)
