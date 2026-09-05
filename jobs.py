import logging

from alerts import (
    alert_is_triggered,
    can_notify,
    format_alert_message,
)
from bot_logic import get_quotes_df
from bb_api import fetch_usdt_rub_rates
from cities import city_keys
from currencies import currency_keys
from db_manager import list_all_alerts, mark_alert_triggered
from history_store import record_history_point

logger = logging.getLogger(__name__)


def evaluate_alerts(alerts: list[dict], rate_for) -> list[dict]:
    due: list[dict] = []
    for alert in alerts:
        rate = rate_for(alert)
        if rate is None:
            continue
        if not alert_is_triggered(
            alert['direction'],
            float(alert['threshold']),
            float(rate),
        ):
            continue
        if not can_notify(alert.get('last_triggered_at')):
            continue
        lang = alert.get('lang') or 'en'
        due.append({
            'id': alert['id'],
            'user_id': alert['user_id'],
            'text': format_alert_message(alert, float(rate), lang),
        })
    return due


def current_cash_buy(city: str, currency: str) -> float | None:
    try:
        frame = get_quotes_df(currency, city, 1)
    except Exception as exc:
        logger.error('Could not load cash rate: %s', exc)
        return None
    if frame is None or frame.empty:
        return None
    value = frame.iloc[0]['buy_quote']
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def current_usdt_rate() -> float | None:
    try:
        result = fetch_usdt_rub_rates()
    except Exception as exc:
        logger.error('Could not load USDT rate: %s', exc)
        return None
    if not result:
        return None
    try:
        return float(result['median'])
    except (KeyError, TypeError, ValueError):
        return None


def rate_for_alert(alert: dict) -> float | None:
    kind = alert.get('kind')
    if kind == 'usdt':
        return current_usdt_rate()
    if kind == 'cash_buy':
        city = alert.get('city')
        currency = alert.get('currency')
        if not city or not currency:
            return None
        return current_cash_buy(city, currency)
    return None


def collect_due_alerts() -> list[dict]:
    return evaluate_alerts(list_all_alerts(), rate_for_alert)


async def check_alerts_job(context) -> None:
    due = collect_due_alerts()
    for item in due:
        try:
            await context.bot.send_message(
                chat_id=item['user_id'],
                text=item['text'],
            )
            mark_alert_triggered(item['id'])
        except Exception as exc:
            logger.error(
                'Could not send alert %s: %s',
                item['id'],
                exc,
            )


def snapshot_history() -> None:
    for city in city_keys():
        for currency in currency_keys():
            rate = current_cash_buy(city, currency)
            if rate is None:
                continue
            record_history_point(city, currency, rate)


async def snapshot_history_job(context) -> None:
    snapshot_history()
