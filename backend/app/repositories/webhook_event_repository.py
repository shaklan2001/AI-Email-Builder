from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from app.core.database import get_database
from app.models.webhook_event import WebhookEvent, WebhookEventType


class WebhookEventRepository:
    COLLECTION = "webhook_events"

    def _doc_to_record(self, doc: dict[str, Any]) -> WebhookEvent:
        created_at = doc.get("created_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        timestamp = doc.get("timestamp")
        if not isinstance(timestamp, datetime):
            timestamp = created_at
        payload = doc.get("payload")
        if not isinstance(payload, dict):
            payload = {}
        return WebhookEvent(
            id=str(doc.get("_id", "")),
            event_id=str(doc["event_id"]),
            event_type=doc["event_type"],  # type: ignore[arg-type]
            timestamp=timestamp,
            recipient=str(doc["recipient"]),
            workflow_id=str(doc["workflow_id"]) if doc.get("workflow_id") else None,
            resend_email_id=str(doc["resend_email_id"]) if doc.get("resend_email_id") else None,
            payload=payload,
            processed=bool(doc.get("processed", False)),
            created_at=created_at,
        )

    async def get_by_event_id(self, event_id: str) -> WebhookEvent | None:
        doc = await get_database()[self.COLLECTION].find_one({"event_id": event_id})
        if doc is None:
            return None
        return self._doc_to_record(doc)

    async def create(
        self,
        *,
        event_id: str,
        event_type: WebhookEventType,
        timestamp: datetime,
        recipient: str,
        workflow_id: str | None = None,
        resend_email_id: str | None = None,
        payload: dict[str, object] | None = None,
        processed: bool = False,
    ) -> WebhookEvent | None:
        now = datetime.now(UTC)
        record_id = str(uuid4())
        doc: dict[str, Any] = {
            "_id": record_id,
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "recipient": recipient,
            "workflow_id": workflow_id,
            "resend_email_id": resend_email_id,
            "payload": payload or {},
            "processed": processed,
            "created_at": now,
        }
        try:
            await get_database()[self.COLLECTION].insert_one(doc)
        except DuplicateKeyError:
            return None
        return self._doc_to_record(doc)

    async def mark_processed(self, record_id: str) -> None:
        await get_database()[self.COLLECTION].update_one(
            {"_id": record_id},
            {"$set": {"processed": True}},
        )


webhook_event_repository = WebhookEventRepository()
