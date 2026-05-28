from collections.abc import Sequence
from typing import Any

import certifi
from beanie import init_beanie
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings
from app.core.logger import get_logger
from app.models import BEANIE_DOCUMENT_MODELS

logger = get_logger(__name__)

_client: AsyncMongoClient | None = None

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
    (
        "workflow_runs",
        [("next_execution_at", 1), ("status", 1)],
        {"name": "idx_runs_due_execution"},
    ),
    (
        "workflow_runs",
        [("workflow_id", 1), ("recipient_id", 1)],
        {"unique": True, "name": "idx_runs_workflow_recipient"},
    ),
    (
        "workflow_runs",
        [("workflow_id", 1), ("status", 1)],
        {"name": "idx_runs_workflow_status"},
    ),
    (
        "executions",
        [("next_execution_at", 1), ("status", 1)],
        {"name": "idx_executions_due_execution"},
    ),
    (
        "executions",
        [("workflow_id", 1), ("lead_id", 1)],
        {"unique": True, "name": "idx_executions_workflow_lead"},
    ),
    (
        "executions",
        [("workflow_id", 1), ("status", 1)],
        {"name": "idx_executions_workflow_status"},
    ),
    (
        "webhook_events",
        [("event_id", 1)],
        {"unique": True, "sparse": True, "name": "idx_webhook_event_id"},
    ),
    (
        "webhook_events",
        [("workflow_id", 1), ("event_type", 1)],
        {"name": "idx_webhook_workflow"},
    ),
    (
        "webhook_events",
        [("processed", 1), ("created_at", 1)],
        {"name": "idx_webhook_processed"},
    ),
    (
        "analytics",
        [("workflow_id", 1)],
        {"unique": True, "name": "idx_analytics_workflow_id"},
    ),
    (
        "email_messages",
        [("resend_message_id", 1)],
        {"unique": True, "name": "idx_email_messages_resend_message_id"},
    ),
    (
        "email_messages",
        [("workflow_id", 1), ("lead_id", 1)],
        {"name": "idx_email_messages_workflow_lead"},
    ),
    (
        "leads",
        [("workflow_id", 1), ("email", 1)],
        {"unique": True, "name": "idx_leads_workflow_email"},
    ),
    (
        "inbound_replies",
        [("workflow_id", 1), ("created_at", -1)],
        {"name": "idx_inbound_replies_workflow_created"},
    ),
    (
        "tool_executions",
        [("workflow_id", 1), ("created_at", -1)],
        {"name": "idx_tool_executions_workflow_created"},
    ),
    (
        "tool_executions",
        [("workflow_id", 1), ("lead_email", 1)],
        {"name": "idx_tool_executions_workflow_lead"},
    ),
)


async def connect_db() -> None:
    global _client
    if _client is not None:
        return
    _client = AsyncMongoClient(
        settings.mongodb_connection_url,
        tlsCAFile=certifi.where(),
    )
    db = _client[settings.mongodb_db_name]
    await ensure_indexes(db)
    await init_beanie(database=db, document_models=BEANIE_DOCUMENT_MODELS)
    logger.info("mongodb_connected", db_name=settings.mongodb_db_name)


async def close_db() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("mongodb_disconnected")


def get_database() -> AsyncDatabase:
    if _client is None:
        raise RuntimeError("MongoDB is not connected")
    return _client[settings.mongodb_db_name]


async def ensure_indexes(db: AsyncDatabase) -> None:
    for collection, keys, options in INDEX_SPECS:
        await db[collection].create_index(keys, **options)
