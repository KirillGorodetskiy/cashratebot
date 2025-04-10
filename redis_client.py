import os
import redis
import logging

logger = logging.getLogger(__name__)

REDIS_CLIENT = None

def redis_client_init():
    global REDIS_CLIENT

    try: 
        # Create and export a shared Redis client
        REDIS_CLIENT = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )
        REDIS_CLIENT.ping()
        logger.info("Redis connected successfully")
    except redis.exceptions.RedisError  as e:
        REDIS_CLIENT = None
        logger.error("Redis is not available: %s", e)
