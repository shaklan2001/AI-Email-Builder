"""Lead records keyed by workflow + email."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import get_database
from app.schemas.enums import LEAD_STATUS_RANK, LeadStatus, normalize_lead_status
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
        auto_reply_count: int,
        human_review_required: bool,
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
        self.auto_reply_count = auto_reply_count
        self.human_review_required = human_review_required
        self.updated_at = updated_at
        self.created_at = created_at


def lead_status_for_reply_intent(intent: ReplyIntent) -> LeadStatus:
    mapping = {
        ReplyIntent.INTERESTED: LeadStatus.INTERESTED,
        ReplyIntent.NOT_INTERESTED: LeadStatus.NOT_INTERESTED,
        ReplyIntent.NEEDS_INFO: LeadStatus.NEEDS_INFO,
        ReplyIntent.BOOK_DEMO: LeadStatus.BOOKED_DEMO,
        ReplyIntent.PRICING: LeadStatus.NEEDS_INFO,
        ReplyIntent.QUESTION: LeadStatus.NEEDS_INFO,
        ReplyIntent.UNSUBSCRIBE: LeadStatus.UNSUBSCRIBED,
        ReplyIntent.UNKNOWN: LeadStatus.REPLIED,
    }
    return mapping.get(intent, LeadStatus.REPLIED)


def _should_upgrade_status(current: LeadStatus, proposed: LeadStatus) -> bool:
    terminal = {LeadStatus.NOT_INTERESTED, LeadStatus.UNSUBSCRIBED, LeadStatus.BOOKED_DEMO}
    if current in terminal:
        return proposed in terminal and LEAD_STATUS_RANK[proposed] >= LEAD_STATUS_RANK[current]
    return LEAD_STATUS_RANK[proposed] >= LEAD_STATUS_RANK[current]


class LeadRepository:
    COLLECTION = "leads"
    MAX_AUTO_REPLIES = 2

    def _doc_to_record(self, doc: dict[str, Any]) -> LeadRecord:
        created_at = doc.get("created_at")
        updated_at = doc.get("updated_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        if not isinstance(updated_at, datetime):
            updated_at = created_at
        status = normalize_lead_status(str(doc.get("status") or LeadStatus.NEW.value))
        return LeadRecord(
            id=str(doc.get("_id", "")),
            workflow_id=str(doc.get("workflow_id") or doc.get("campaign_id", "")),
            email=str(doc["email"]).lower(),
            campaign_id=str(doc.get("campaign_id") or doc.get("workflow_id", "")),
            status=status.value,
            reply_intent=str(doc["reply_intent"]) if doc.get("reply_intent") else None,
            last_reply_body=str(doc["last_reply_body"]) if doc.get("last_reply_body") else None,
            auto_reply_count=int(doc.get("auto_reply_count") or 0),
            human_review_required=bool(doc.get("human_review_required", False)),
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
        increment_auto_reply: bool = False,
        human_review_required: bool | None = None,
    ) -> LeadRecord:
        now = datetime.now(UTC)
        normalized_email = email.lower()
        status_value = normalize_lead_status(status)
        intent_value = None
        if reply_intent is not None:
            intent_value = (
                reply_intent.value
                if isinstance(reply_intent, ReplyIntent)
                else str(reply_intent)
            )

        existing = await self.find_by_workflow_and_email(workflow_id, normalized_email)
        if existing is not None:
            current_status = normalize_lead_status(existing.status)
            next_status = (
                status_value
                if _should_upgrade_status(current_status, status_value)
                else current_status
            )
            update_fields: dict[str, Any] = {
                "status": next_status.value,
                "updated_at": now,
                "workflow_id": workflow_id,
                "campaign_id": workflow_id,
            }
            if intent_value is not None:
                update_fields["reply_intent"] = intent_value
            if last_reply_body is not None:
                update_fields["last_reply_body"] = last_reply_body
            if increment_auto_reply:
                update_fields["auto_reply_count"] = existing.auto_reply_count + 1
            if human_review_required is not None:
                update_fields["human_review_required"] = human_review_required
            elif increment_auto_reply and existing.auto_reply_count + 1 >= self.MAX_AUTO_REPLIES:
                update_fields["human_review_required"] = True

            result = await get_database()[self.COLLECTION].find_one_and_update(
                {"_id": existing.id},
                {"$set": update_fields},
                return_document=True,
            )
            assert result is not None
            return self._doc_to_record(result)

        auto_count = 1 if increment_auto_reply else 0
        doc_id = str(uuid4())
        doc: dict[str, Any] = {
            "_id": doc_id,
            "workflow_id": workflow_id,
            "campaign_id": workflow_id,
            "email": normalized_email,
            "status": status_value.value,
            "reply_intent": intent_value,
            "last_reply_body": last_reply_body,
            "auto_reply_count": auto_count,
            "human_review_required": bool(human_review_required)
            or auto_count >= self.MAX_AUTO_REPLIES,
            "created_at": now,
            "updated_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return self._doc_to_record(doc)

    async def update_status_for_event(
        self,
        *,
        workflow_id: str,
        email: str,
        status: LeadStatus,
    ) -> LeadRecord | None:
        existing = await self.find_by_workflow_and_email(workflow_id, email)
        if existing is None:
            return await self.upsert_for_workflow(
                workflow_id=workflow_id,
                email=email,
                status=status,
            )
        current = normalize_lead_status(existing.status)
        if not _should_upgrade_status(current, status):
            return existing
        return await self.upsert_for_workflow(
            workflow_id=workflow_id,
            email=email,
            status=status,
        )

    async def count_by_status(self, workflow_id: str) -> dict[str, int]:
        pipeline = [
            {"$match": {"workflow_id": workflow_id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        cursor = get_database()[self.COLLECTION].aggregate(pipeline)
        rows = await cursor.to_list(length=None)
        counts: dict[str, int] = {}
        for row in rows:
            raw_status = row.get("_id")
            if isinstance(raw_status, str):
                normalized = normalize_lead_status(raw_status)
                counts[normalized.value] = counts.get(normalized.value, 0) + int(row.get("count", 0))
        return counts


lead_repository = LeadRepository()
