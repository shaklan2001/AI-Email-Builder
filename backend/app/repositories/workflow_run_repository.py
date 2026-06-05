from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import get_database
from app.models.workflow_run import WorkflowRun, WorkflowRunStatus


class WorkflowRunRepository:
    COLLECTION = "workflow_runs"

    def _doc_to_record(self, doc: dict[str, Any]) -> WorkflowRun:
        run_id = str(doc.get("_id", ""))
        created_at = doc.get("created_at")
        updated_at = doc.get("updated_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        if not isinstance(updated_at, datetime):
            updated_at = created_at
        next_execution_at = doc.get("next_execution_at")
        if next_execution_at is not None and not isinstance(next_execution_at, datetime):
            next_execution_at = None
        return WorkflowRun(
            id=run_id,
            workflow_id=str(doc["workflow_id"]),
            recipient_id=str(doc["recipient_id"]),
            current_step=str(doc["current_step"]),
            status=doc["status"],  # type: ignore[arg-type]
            next_execution_at=next_execution_at,
            created_at=created_at,
            updated_at=updated_at,
        )

    async def create(
        self,
        *,
        workflow_id: str,
        recipient_id: str,
        current_step: str,
        status: WorkflowRunStatus = "queued",
        next_execution_at: datetime | None = None,
    ) -> WorkflowRun:
        now = datetime.now(UTC)
        run_id = str(uuid4())
        doc: dict[str, Any] = {
            "_id": run_id,
            "workflow_id": workflow_id,
            "recipient_id": recipient_id,
            "current_step": current_step,
            "status": status,
            "next_execution_at": next_execution_at,
            "created_at": now,
            "updated_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return self._doc_to_record(doc)

    async def get_by_id(self, run_id: str) -> WorkflowRun | None:
        doc = await get_database()[self.COLLECTION].find_one({"_id": run_id})
        if doc is None:
            return None
        return self._doc_to_record(doc)

    async def update(
        self,
        run_id: str,
        *,
        current_step: str | None = None,
        status: WorkflowRunStatus | None = None,
        next_execution_at: datetime | None = ...,  # type: ignore[assignment]
    ) -> WorkflowRun | None:
        updates: dict[str, Any] = {"updated_at": datetime.now(UTC)}
        if current_step is not None:
            updates["current_step"] = current_step
        if status is not None:
            updates["status"] = status
        if next_execution_at is not ...:
            updates["next_execution_at"] = next_execution_at

        result = await get_database()[self.COLLECTION].find_one_and_update(
            {"_id": run_id},
            {"$set": updates},
            return_document=True,
        )
        if result is None:
            return None
        return self._doc_to_record(result)

    async def find_due(
        self,
        *,
        as_of: datetime,
        limit: int = 500,
    ) -> list[WorkflowRun]:
        cursor = (
            get_database()[self.COLLECTION]
            .find(
                {
                    "status": {"$in": ["queued", "waiting"]},
                    "next_execution_at": {"$lte": as_of},
                },
            )
            .limit(limit)
        )
        return [self._doc_to_record(doc) async for doc in cursor]

    async def find_pending_by_workflow(self, workflow_id: str) -> list[WorkflowRun]:
        cursor = get_database()[self.COLLECTION].find(
            {
                "workflow_id": workflow_id,
                "status": {"$in": ["queued", "running", "waiting"]},
            },
        )
        return [self._doc_to_record(doc) async for doc in cursor]

    async def find_by_workflow_and_recipient(
        self,
        workflow_id: str,
        recipient_id: str,
    ) -> WorkflowRun | None:
        doc = await get_database()[self.COLLECTION].find_one(
            {"workflow_id": workflow_id, "recipient_id": recipient_id},
        )
        if doc is None:
            return None
        return self._doc_to_record(doc)

    async def find_active_by_recipient(self, recipient_id: str) -> list[WorkflowRun]:
        cursor = (
            get_database()[self.COLLECTION]
            .find(
                {
                    "recipient_id": recipient_id,
                    "status": {"$in": ["queued", "running", "waiting"]},
                },
            )
            .sort("updated_at", -1)
        )
        return [self._doc_to_record(doc) async for doc in cursor]


workflow_run_repository = WorkflowRunRepository()
