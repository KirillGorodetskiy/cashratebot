import os
import redis
import logging

logger = logging.getLogger(__name__)

# Is Redis is not active it will take some time to get response and error
# we use REDIS_AVAILABLE
REDIS_AVAILABLE: bool = True

# Create and export a shared Redis client
REDIS_CLIENT = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )


def redis_client_init() -> None:
    global REDIS_AVAILABLE
    try:
        REDIS_CLIENT.ping()
        logger.info("Redis connected successfully")
    except redis.RedisError as e:
        REDIS_AVAILABLE = False
        logger.error("Redis is not available: %s", e)
