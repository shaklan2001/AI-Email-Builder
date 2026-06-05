"""Outbound email records keyed by Resend message id."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import get_database


class EmailMessageRecord:
    def __init__(
        self,
        *,
        id: str,
        resend_message_id: str,
        workflow_id: str,
        lead_id: str,
        step_id: str | None,
        sent: bool,
        delivered: bool,
        opened: bool,
        clicked: bool,
        replied: bool,
        failed: bool,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.resend_message_id = resend_message_id
        self.workflow_id = workflow_id
        self.lead_id = lead_id
        self.step_id = step_id
        self.sent = sent
        self.delivered = delivered
        self.opened = opened
        self.clicked = clicked
        self.replied = replied
        self.failed = failed
        self.created_at = created_at
        self.updated_at = updated_at


class EmailMessageRepository:
    COLLECTION = "email_messages"

    def _doc_to_record(self, doc: dict[str, Any]) -> EmailMessageRecord:
        created_at = doc.get("created_at")
        updated_at = doc.get("updated_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        if not isinstance(updated_at, datetime):
            updated_at = created_at
        return EmailMessageRecord(
            id=str(doc.get("_id", "")),
            resend_message_id=str(doc["resend_message_id"]),
            workflow_id=str(doc["workflow_id"]),
            lead_id=str(doc["lead_id"]),
            step_id=str(doc["step_id"]) if doc.get("step_id") else None,
            sent=bool(doc.get("sent", False)),
            delivered=bool(doc.get("delivered", False)),
            opened=bool(doc.get("opened", False)),
            clicked=bool(doc.get("clicked", False)),
            replied=bool(doc.get("replied", False)),
            failed=bool(doc.get("failed", False)),
            created_at=created_at,
            updated_at=updated_at,
        )

    async def create_sent(
        self,
        *,
        resend_message_id: str,
        workflow_id: str,
        lead_id: str,
        step_id: str | None = None,
    ) -> EmailMessageRecord:
        now = datetime.now(UTC)
        doc_id = str(uuid4())
        doc: dict[str, Any] = {
            "_id": doc_id,
            "resend_message_id": resend_message_id,
            "workflow_id": workflow_id,
            "lead_id": lead_id,
            "step_id": step_id,
            "sent": True,
            "delivered": False,
            "opened": False,
            "clicked": False,
            "replied": False,
            "failed": False,
            "created_at": now,
            "updated_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return self._doc_to_record(doc)

    async def create_failed(
        self,
        *,
        workflow_id: str,
        lead_id: str,
        step_id: str | None = None,
    ) -> EmailMessageRecord:
        now = datetime.now(UTC)
        doc_id = str(uuid4())
        doc: dict[str, Any] = {
            "_id": doc_id,
            "resend_message_id": f"failed_{doc_id}",
            "workflow_id": workflow_id,
            "lead_id": lead_id,
            "step_id": step_id,
            "sent": False,
            "delivered": False,
            "opened": False,
            "clicked": False,
            "replied": False,
            "failed": True,
            "created_at": now,
            "updated_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return self._doc_to_record(doc)

    async def get_by_resend_message_id(
        self,
        resend_message_id: str,
    ) -> EmailMessageRecord | None:
        doc = await get_database()[self.COLLECTION].find_one(
            {"resend_message_id": resend_message_id},
        )
        if doc is None:
            return None
        return self._doc_to_record(doc)

    async def apply_tracking_event(
        self,
        resend_message_id: str,
        *,
        event: str,
    ) -> EmailMessageRecord | None:
        field_map = {
            "delivered": "delivered",
            "opened": "opened",
            "clicked": "clicked",
            "replied": "replied",
            "bounced": "failed",
            "failed": "failed",
        }
        field = field_map.get(event)
        if field is None:
            return await self.get_by_resend_message_id(resend_message_id)

        now = datetime.now(UTC)
        result = await get_database()[self.COLLECTION].find_one_and_update(
            {"resend_message_id": resend_message_id},
            {"$set": {field: True, "updated_at": now}},
            return_document=True,
        )
        if result is None:
            return None
        return self._doc_to_record(result)

    async def count_for_workflow(self, workflow_id: str) -> int:
        return await get_database()[self.COLLECTION].count_documents(
            {"workflow_id": workflow_id},
        )


email_message_repository = EmailMessageRepository()
