import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

COOLDOWN = timedelta(hours=6)


def alert_is_triggered(
    direction: str,
    threshold: float,
    rate: float,
) -> bool:
    if direction == 'below':
        return rate <= threshold
    if direction == 'above':
        return rate >= threshold
    return False


def can_notify(last_triggered_at: datetime | None) -> bool:
    if last_triggered_at is None:
        return True
    if last_triggered_at.tzinfo is None:
        last_triggered_at = last_triggered_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - last_triggered_at >= COOLDOWN


def format_alert_message(alert: dict, rate: float, lang: str) -> str:
    target = alert.get('currency') or 'USDT'
    city = alert.get('city') or ''
    if lang == 'ru':
        return (
            f'🔔 Алерт: {target} {city} {rate:.2f} '
            f'({alert["direction"]} {alert["threshold"]:.2f})'
        )
    return (
        f'🔔 Alert: {target} {city} {rate:.2f} '
        f'({alert["direction"]} {alert["threshold"]:.2f})'
    )
