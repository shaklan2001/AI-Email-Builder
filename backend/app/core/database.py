from collections.abc import Sequence
from typing import Any

import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_client: AsyncIOMotorClient | None = None

IndexSpec = tuple[str, list[tuple[str, int]], dict[str, Any]]

INDEX_SPECS: Sequence[IndexSpec] = (
    (
        "conversations",
        [("user_id", 1), ("updated_at", -1)],
        {"name": "idx_conversations_user_id"},
    ),
    (
        "conversations",
        [("workflow_id", 1)],
        {"sparse": True, "name": "idx_conversations_workflow_id"},
    ),
    (
        "conversations",
        [("user_id", 1), ("workflow_id", 1)],
        {"unique": True, "name": "idx_conversations_user_workflow"},
    ),
    (
        "workflows",
        [("user_id", 1), ("status", 1)],
        {"name": "idx_workflows_user_status"},
    ),
    (
        "workflows",
        [("user_id", 1), ("updated_at", -1)],
        {"name": "idx_workflows_user_updated"},
    ),
)


async def connect_db() -> None:
    global _client
    _client = AsyncIOMotorClient(
        settings.mongodb_connection_url,
        tlsCAFile=certifi.where(),
    )
    db = _client[settings.mongodb_db_name]
    await ensure_indexes(db)
    logger.info("mongodb_connected", db_name=settings.mongodb_db_name)


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("mongodb_disconnected")


def get_database() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("MongoDB is not connected")
    return _client[settings.mongodb_db_name]


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    for collection, keys, options in INDEX_SPECS:
        await db[collection].create_index(keys, **options)
