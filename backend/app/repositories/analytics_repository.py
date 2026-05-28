from datetime import UTC, datetime
from typing import Any

from app.core.database import get_database
from app.models.analytics import WorkflowAnalytics

ANALYTICS_METRICS = (
    "sent",
    "delivered",
    "opened",
    "clicked",
    "replied",
    "failed",
    "bounced",
)


class AnalyticsRepository:
    COLLECTION = "analytics"

    def _doc_to_record(self, doc: dict[str, Any]) -> WorkflowAnalytics:
        updated_at = doc.get("updated_at")
        if not isinstance(updated_at, datetime):
            updated_at = datetime.now(UTC)
        return WorkflowAnalytics(
            workflow_id=str(doc["workflow_id"]),
            sent=int(doc.get("sent", 0)),
            delivered=int(doc.get("delivered", 0)),
            opened=int(doc.get("opened", 0)),
            clicked=int(doc.get("clicked", 0)),
            replied=int(doc.get("replied", 0)),
            failed=int(doc.get("failed", 0)),
            bounced=int(doc.get("bounced", 0)),
            updated_at=updated_at,
        )

    async def increment(
        self,
        workflow_id: str,
        *,
        metric: str,
        amount: int = 1,
    ) -> WorkflowAnalytics:
        if metric not in ANALYTICS_METRICS:
            msg = f"Invalid analytics metric: {metric}"
            raise ValueError(msg)
        if amount < 1:
            msg = "Increment amount must be at least 1"
            raise ValueError(msg)

        now = datetime.now(UTC)
        collection = get_database()[self.COLLECTION]
        # Two-step upsert avoids ConflictingUpdateOperators when $inc and $setOnInsert
        # both touch counter fields on insert.
        await collection.update_one(
            {"workflow_id": workflow_id},
            {
                "$setOnInsert": {
                    "workflow_id": workflow_id,
                    "sent": 0,
                    "delivered": 0,
                    "opened": 0,
                    "clicked": 0,
                    "replied": 0,
                    "failed": 0,
                    "bounced": 0,
                },
            },
            upsert=True,
        )
        doc = await collection.find_one_and_update(
            {"workflow_id": workflow_id},
            {"$inc": {metric: amount}, "$set": {"updated_at": now}},
            return_document=True,
        )
        assert doc is not None
        return self._doc_to_record(doc)

    async def get_by_workflow_id(self, workflow_id: str) -> WorkflowAnalytics | None:
        doc = await get_database()[self.COLLECTION].find_one({"workflow_id": workflow_id})
        if doc is None:
            return None
        return self._doc_to_record(doc)


analytics_repository = AnalyticsRepository()
