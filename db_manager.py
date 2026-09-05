# -*- coding: utf-8 -*-
import logging
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

from cities import city_keys
from currencies import currency_keys

logger = logging.getLogger(__name__)

load_dotenv(encoding='utf-8')

ALLOWED_COUNTERS = frozenset({
    'filled_requests_currencies',
    'filled_requests_stats',
})
ALLOWED_ALERT_KINDS = frozenset({'cash_buy', 'usdt'})
ALLOWED_ALERT_DIRS = frozenset({'below', 'above'})
MAX_ALERTS = 10


# Database connection setup
def get_db_connection() -> None:
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        logger.error('Couldn`t connect to db %s', e)
        return None


def db_init() -> None:
    """Initialize database (create tables if not exist)"""
    conn = get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cur:
                # Create the 'users' table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGINT PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        username TEXT,
                        language_code TEXT,
                        is_bot BOOLEAN,
                        created_at TIMESTAMP DEFAULT NOW(),
                        filled_requests_currencies INTEGER DEFAULT 0,
                        filled_requests_stats INTEGER DEFAULT 0
                    );
                """)
                cur.execute(
                    'ALTER TABLE users '
                    'ADD COLUMN IF NOT EXISTS last_city TEXT'
                )
                cur.execute(
                    'ALTER TABLE users '
                    'ADD COLUMN IF NOT EXISTS last_currency TEXT'
                )
                cur.execute(
                    'ALTER TABLE users '
                    'ADD COLUMN IF NOT EXISTS fav_city TEXT'
                )
                cur.execute(
                    'ALTER TABLE users '
                    'ADD COLUMN IF NOT EXISTS fav_currency TEXT'
                )
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        kind TEXT NOT NULL,
                        city TEXT,
                        currency TEXT,
                        direction TEXT NOT NULL,
                        threshold DOUBLE PRECISION NOT NULL,
                        last_triggered_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                conn.commit()
                logger.info("Database initialized: 'users' table checked/created.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
        finally:
            conn.close()
    else:
        logger.error("Couldn`t init DB because conn is not available")


def save_new_user_data_in_db(user, conn=None) -> None:
    """Save new user data in the database"""
    conn = conn or get_db_connection()  # Use passed conn or create a new one
    if conn is not None:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE id = %s", (user.id,))
                if not cur.fetchone():  # If the user doesn't exist
                    cur.execute("""
                        INSERT INTO users (id, first_name, last_name, username, language_code, is_bot, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        user.id,
                        user.first_name,
                        user.last_name,
                        user.username,
                        user.language_code,
                        user.is_bot
                    ))
                    conn.commit()
                    logger.info(f"User {user.id} saved to database successfully.")
                else:
                    logger.info(f"User {user.id} already exists in the database.")
        except Exception as e:
            logger.error(f"Error saving user {user.id} to database: {e}")
        finally:
            conn.close()
    else:
        logger.error('DB is not available to save user.id {} in db'.format(user.id))


def increment_field_db(user, field_name: str, conn=None) -> None:
    """Increment a field (e.g., request_count) in the users table"""
    if field_name not in ALLOWED_COUNTERS:
        logger.error('Rejected increment for field %s', field_name)
        return
    conn = conn or get_db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cur:
                # Dynamically create a SQL statement
                cur.execute("SELECT 1 FROM users WHERE id = %s", (user.id,))
                if cur.fetchone():
                    cur.execute(
                        sql.SQL("UPDATE users SET {0} = {0} + 1 WHERE id = %s;").format(
                            sql.Identifier(field_name)
                        ),
                        (user.id,)
                    )
                    conn.commit()
                    logger.info(f"Field '{field_name}' incremented for user {user.id}.")
                else:
                    logger.warning(f"User {user.id} not found for increment operation.")
        except Exception as e:
            logger.error(f"Error incrementing {field_name} for user {user.id}: {e}")
        finally:
            conn.close()
    else:
        logger.error('DB is not available to increment field {} for user.id {}'.format(field_name, user.id))


def _empty_prefs() -> dict:
    return {
        'last_city': None,
        'last_currency': None,
        'fav_city': None,
        'fav_currency': None,
    }


def get_user_prefs(user_id: int) -> dict:
    conn = get_db_connection()
    if conn is None:
        return _empty_prefs()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT last_city, last_currency, '
                'fav_city, fav_currency '
                'FROM users WHERE id = %s',
                (user_id,),
            )
            row = cur.fetchone()
    except Exception as exc:
        logger.error('Could not read prefs for %s: %s', user_id, exc)
        return _empty_prefs()
    finally:
        conn.close()
    if row is None:
        return _empty_prefs()
    return {
        'last_city': row[0],
        'last_currency': row[1],
        'fav_city': row[2],
        'fav_currency': row[3],
    }


def set_last_lookup(user_id: int, city: str, currency: str) -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error('DB is not available to save last lookup')
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE users SET last_city = %s, '
                'last_currency = %s WHERE id = %s',
                (city, currency, user_id),
            )
            conn.commit()
    except Exception as exc:
        logger.error('Could not save last lookup: %s', exc)
    finally:
        conn.close()


def set_favorite(user_id: int, city: str, currency: str) -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error('DB is not available to save favorite')
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE users SET fav_city = %s, '
                'fav_currency = %s WHERE id = %s',
                (city, currency, user_id),
            )
            conn.commit()
    except Exception as exc:
        logger.error('Could not save favorite: %s', exc)
    finally:
        conn.close()


def count_alerts(user_id: int) -> int:
    conn = get_db_connection()
    if conn is None:
        return 0
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT COUNT(*) FROM alerts WHERE user_id = %s',
                (user_id,),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0
    except Exception as exc:
        logger.error('Could not count alerts: %s', exc)
        return 0
    finally:
        conn.close()


def _validate_alert(
    kind: str,
    city: str | None,
    currency: str | None,
    direction: str,
) -> None:
    if kind not in ALLOWED_ALERT_KINDS:
        raise ValueError(f'Unknown alert kind: {kind}')
    if direction not in ALLOWED_ALERT_DIRS:
        raise ValueError(f'Unknown alert direction: {direction}')
    if kind == 'cash_buy':
        if city not in city_keys() or currency not in currency_keys():
            raise ValueError('Unknown city or currency')
    if kind == 'usdt' and currency not in {None, '', 'USDT'}:
        raise ValueError('USDT alert currency must be USDT')


def create_alert(
    user_id: int,
    kind: str,
    city: str | None,
    currency: str | None,
    direction: str,
    threshold: float,
) -> bool:
    _validate_alert(kind, city, currency, direction)
    if threshold <= 0 or threshold > 1_000_000:
        raise ValueError('Invalid alert threshold')
    if count_alerts(user_id) >= MAX_ALERTS:
        return False
    conn = get_db_connection()
    if conn is None:
        logger.error('DB is not available to create alert')
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO alerts '
                '(user_id, kind, city, currency, direction, threshold) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (user_id, kind, city, currency, direction, threshold),
            )
            conn.commit()
        return True
    except Exception as exc:
        logger.error('Could not create alert: %s', exc)
        return False
    finally:
        conn.close()


def delete_alert(user_id: int, alert_id: int) -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error('DB is not available to delete alert')
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM alerts WHERE id = %s AND user_id = %s',
                (alert_id, user_id),
            )
            conn.commit()
    except Exception as exc:
        logger.error('Could not delete alert: %s', exc)
    finally:
        conn.close()


def list_alerts(user_id: int) -> list[dict]:
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, kind, city, currency, direction, '
                'threshold FROM alerts WHERE user_id = %s '
                'ORDER BY id',
                (user_id,),
            )
            rows = cur.fetchall()
    except Exception as exc:
        logger.error('Could not list alerts: %s', exc)
        return []
    finally:
        conn.close()
    return [
        {
            'id': row[0],
            'kind': row[1],
            'city': row[2],
            'currency': row[3],
            'direction': row[4],
            'threshold': row[5],
        }
        for row in rows
    ]


def list_all_alerts() -> list[dict]:
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT a.id, a.user_id, a.kind, a.city, a.currency, '
                'a.direction, a.threshold, a.last_triggered_at, '
                'u.language_code '
                'FROM alerts a '
                'LEFT JOIN users u ON u.id = a.user_id'
            )
            rows = cur.fetchall()
    except Exception as exc:
        logger.error('Could not list all alerts: %s', exc)
        return []
    finally:
        conn.close()
    result = []
    for row in rows:
        lang = 'ru' if row[8] and str(row[8]).startswith('ru') else 'en'
        result.append({
            'id': row[0],
            'user_id': row[1],
            'kind': row[2],
            'city': row[3],
            'currency': row[4],
            'direction': row[5],
            'threshold': row[6],
            'last_triggered_at': row[7],
            'lang': lang,
        })
    return result


def mark_alert_triggered(alert_id: int) -> None:
    conn = get_db_connection()
    if conn is None:
        logger.error('DB is not available to mark alert')
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE alerts SET last_triggered_at = NOW() '
                'WHERE id = %s',
                (alert_id,),
            )
            conn.commit()
    except Exception as exc:
        logger.error('Could not mark alert: %s', exc)
    finally:
        conn.close()