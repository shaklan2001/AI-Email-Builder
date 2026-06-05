"""Lead records keyed by workflow + email."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import get_database
from app.schemas.enums import LeadStatus
from app.schemas.reply_intent import ReplyIntent


class LeadRecord:
    def __init__(
        self,
        *,
        id: str,
        workflow_id: str,
        email: str,
        campaign_id: str,
        status: str,
        reply_intent: str | None,
        last_reply_body: str | None,
        updated_at: datetime,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.workflow_id = workflow_id
        self.email = email
        self.campaign_id = campaign_id
        self.status = status
        self.reply_intent = reply_intent
        self.last_reply_body = last_reply_body
        self.updated_at = updated_at
        self.created_at = created_at


def lead_status_for_reply_intent(intent: ReplyIntent) -> LeadStatus:
    mapping = {
        ReplyIntent.INTERESTED: LeadStatus.INTERESTED,
        ReplyIntent.NOT_INTERESTED: LeadStatus.NOT_INTERESTED,
        ReplyIntent.NEED_MORE_INFO: LeadStatus.REPLIED,
        ReplyIntent.BOOK_DEMO: LeadStatus.BOOKED_DEMO,
    }
    return mapping[intent]


class LeadRepository:
    COLLECTION = "leads"

    def _doc_to_record(self, doc: dict[str, Any]) -> LeadRecord:
        created_at = doc.get("created_at")
        updated_at = doc.get("updated_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        if not isinstance(updated_at, datetime):
            updated_at = created_at
        return LeadRecord(
            id=str(doc.get("_id", "")),
            workflow_id=str(doc.get("workflow_id") or doc.get("campaign_id", "")),
            email=str(doc["email"]).lower(),
            campaign_id=str(doc.get("campaign_id") or doc.get("workflow_id", "")),
            status=str(doc.get("status") or LeadStatus.PENDING.value),
            reply_intent=str(doc["reply_intent"]) if doc.get("reply_intent") else None,
            last_reply_body=str(doc["last_reply_body"]) if doc.get("last_reply_body") else None,
            updated_at=updated_at,
            created_at=created_at,
        )

    async def find_by_workflow_and_email(
        self,
        workflow_id: str,
        email: str,
    ) -> LeadRecord | None:
        doc = await get_database()[self.COLLECTION].find_one(
            {"workflow_id": workflow_id, "email": email.lower()},
        )
        if doc is None:
            doc = await get_database()[self.COLLECTION].find_one(
                {"campaign_id": workflow_id, "email": email.lower()},
            )
        if doc is None:
            return None
        return self._doc_to_record(doc)

    async def upsert_for_workflow(
        self,
        *,
        workflow_id: str,
        email: str,
        status: LeadStatus | str,
        reply_intent: ReplyIntent | str | None = None,
        last_reply_body: str | None = None,
    ) -> LeadRecord:
        now = datetime.now(UTC)
        normalized_email = email.lower()
        status_value = status.value if isinstance(status, LeadStatus) else str(status)
        intent_value = None
        if reply_intent is not None:
            intent_value = (
                reply_intent.value
                if isinstance(reply_intent, ReplyIntent)
                else str(reply_intent)
            )

        existing = await self.find_by_workflow_and_email(workflow_id, normalized_email)
        if existing is not None:
            update_fields: dict[str, Any] = {
                "status": status_value,
                "updated_at": now,
                "workflow_id": workflow_id,
            }
            if intent_value is not None:
                update_fields["reply_intent"] = intent_value
            if last_reply_body is not None:
                update_fields["last_reply_body"] = last_reply_body
            result = await get_database()[self.COLLECTION].find_one_and_update(
                {"_id": existing.id},
                {"$set": update_fields},
                return_document=True,
            )
            assert result is not None
            return self._doc_to_record(result)

        doc_id = str(uuid4())
        doc: dict[str, Any] = {
            "_id": doc_id,
            "workflow_id": workflow_id,
            "campaign_id": workflow_id,
            "email": normalized_email,
            "status": status_value,
            "reply_intent": intent_value,
            "last_reply_body": last_reply_body,
            "created_at": now,
            "updated_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return self._doc_to_record(doc)


lead_repository = LeadRepository()
