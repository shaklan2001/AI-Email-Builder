import redis.asyncio as redis

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


async def ping_redis() -> bool:
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        return bool(await client.ping())
    except Exception:
        logger.warning("redis_ping_failed", redis_url=settings.redis_url)
        return False
    finally:
        await client.aclose()
