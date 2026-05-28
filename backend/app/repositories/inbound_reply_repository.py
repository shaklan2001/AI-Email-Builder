"""Inbound reply records from Resend webhooks."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import get_database
from app.schemas.reply_intent import ReplyIntent


class InboundReplyRecord:
    def __init__(
        self,
        *,
        id: str,
        workflow_id: str,
        lead_email: str,
        reply_intent: str,
        reply_body: str,
        reply_subject: str | None,
        webhook_event_id: str | None,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.workflow_id = workflow_id
        self.lead_email = lead_email
        self.reply_intent = reply_intent
        self.reply_body = reply_body
        self.reply_subject = reply_subject
        self.webhook_event_id = webhook_event_id
        self.created_at = created_at


class InboundReplyRepository:
    COLLECTION = "inbound_replies"

    def _doc_to_record(self, doc: dict[str, Any]) -> InboundReplyRecord:
        created_at = doc.get("created_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        return InboundReplyRecord(
            id=str(doc.get("_id", "")),
            workflow_id=str(doc["workflow_id"]),
            lead_email=str(doc["lead_email"]),
            reply_intent=str(doc["reply_intent"]),
            reply_body=str(doc.get("reply_body") or ""),
            reply_subject=str(doc["reply_subject"]) if doc.get("reply_subject") else None,
            webhook_event_id=str(doc["webhook_event_id"])
            if doc.get("webhook_event_id")
            else None,
            created_at=created_at,
        )

    async def create(
        self,
        *,
        workflow_id: str,
        lead_email: str,
        reply_intent: ReplyIntent | str,
        reply_body: str,
        reply_subject: str | None = None,
        webhook_event_id: str | None = None,
    ) -> InboundReplyRecord:
        now = datetime.now(UTC)
        doc_id = str(uuid4())
        intent_value = (
            reply_intent.value if isinstance(reply_intent, ReplyIntent) else str(reply_intent)
        )
        doc: dict[str, Any] = {
            "_id": doc_id,
            "workflow_id": workflow_id,
            "lead_email": lead_email.lower(),
            "reply_intent": intent_value,
            "reply_body": reply_body,
            "reply_subject": reply_subject,
            "webhook_event_id": webhook_event_id,
            "created_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return self._doc_to_record(doc)


inbound_reply_repository = InboundReplyRepository()
