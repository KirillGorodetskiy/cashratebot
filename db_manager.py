# -*- coding: utf-8 -*-

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

import logging

logger = logging.getLogger(__name__)

load_dotenv(encoding='utf-8')

# Database connection setup
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )

def db_init():
    """Initialize database (create tables if not exist)"""
    conn = get_db_connection()
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
            conn.commit()
            logger.info("Database initialized: 'users' table checked/created.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        conn.close()



def save_new_user_data_in_db(user, conn=None):
    """Save new user data in the database"""
    conn = conn or get_db_connection()  # Use passed conn or create a new one
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

def increment_field_db(user, field_name, conn=None):
    """Increment a field (e.g., request_count) in the users table"""
    conn = conn or get_db_connection()
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