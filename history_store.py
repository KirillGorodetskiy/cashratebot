import json
import logging
import time

import redis_client

logger = logging.getLogger(__name__)

BARS = '▁▂▃▄▅▆▇█'
MAX_POINTS = 168


def sparkline(values: list[float], width: int = 8) -> str:
    if not values:
        return ''
    if len(values) > width:
        step = len(values) / width
        sampled = [
            values[int(index * step)]
            for index in range(width)
        ]
    else:
        sampled = values
    low = min(sampled)
    high = max(sampled)
    if high == low:
        return BARS[0] * len(sampled)
    chars = []
    for value in sampled:
        pos = (value - low) / (high - low)
        chars.append(BARS[int(pos * (len(BARS) - 1))])
    return ''.join(chars)


def _key(city: str, currency: str) -> str:
    return f'hist:v1:{city.lower()}:{currency.lower()}'


def record_history_point(city: str, currency: str, buy: float) -> None:
    if not redis_client.REDIS_AVAILABLE or not redis_client.REDIS_CLIENT:
        return
    try:
        payload = json.dumps({'t': int(time.time()), 'buy': float(buy)})
        key = _key(city, currency)
        redis_client.REDIS_CLIENT.lpush(key, payload)
        redis_client.REDIS_CLIENT.ltrim(key, 0, MAX_POINTS - 1)
        redis_client.REDIS_CLIENT.expire(key, 8 * 24 * 3600)
    except Exception as exc:
        logger.error('Could not save history: %s', exc)


def load_history(city: str, currency: str) -> list[dict]:
    if not redis_client.REDIS_AVAILABLE or not redis_client.REDIS_CLIENT:
        return []
    try:
        raw = redis_client.REDIS_CLIENT.lrange(
            _key(city, currency),
            0,
            MAX_POINTS - 1,
        )
    except Exception as exc:
        logger.error('Could not load history: %s', exc)
        return []
    points = []
    for item in reversed(raw):
        try:
            points.append(json.loads(item))
        except json.JSONDecodeError:
            continue
    return points


def summarize_history(points: list[dict], lang: str) -> str:
    values = [float(item['buy']) for item in points if 'buy' in item]
    if not values:
        return ''
    line = sparkline(values)
    low = min(values)
    high = max(values)
    if lang == 'ru':
        return f'{line}  {low:.2f}–{high:.2f}'
    return f'{line}  {low:.2f}–{high:.2f}'
