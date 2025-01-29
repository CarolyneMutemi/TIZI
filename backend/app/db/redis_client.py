import aioredis as redis
from aioredis.exceptions import RedisError
from app.core.config import REDIS_HOST


try:
    # Connect to Redis
    redis_client = redis.Redis(host=REDIS_HOST)

except ConnectionError as e:
    # Handle connection error (e.g., retry, log, alert)
    raise redis.ConnectionError("Failed to connect to Redis: Connection Error.") from e

except TimeoutError as e:
    # Handle timeout error (e.g., retry, log, alert)
    raise redis.TimeoutError("Failed to connect to Redis: Timeout Error.") from e

except RedisError as e:
    # Handle other Redis errors
    raise redis.RedisError(f"Failed to connect to Redis: {e}.") from e

async def test_redis_connection(rclient: redis.Redis):
    """
    Test the connection to Redis.
    """
    try:
        pong = await rclient.ping()
        if pong:
            print("Successfully connected to Redis!")
    except RedisError as e:
        raise redis.RedisError(f"Failed to ping Redis: {e}.") from e
