"""Per-lead execution records created when a workflow is activated."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import get_database
from app.schemas.enums import ExecutionStatus


class ExecutionRecord:
    def __init__(
        self,
        *,
        id: str,
        workflow_id: str,
        lead_id: str,
        current_step_id: str,
        status: str,
        workflow_version: int,
        next_execution_at: datetime | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.workflow_id = workflow_id
        self.lead_id = lead_id
        self.current_step_id = current_step_id
        self.status = status
        self.workflow_version = workflow_version
        self.next_execution_at = next_execution_at
        self.created_at = created_at
        self.updated_at = updated_at


class ExecutionRepository:
    COLLECTION = "executions"

    def _doc_to_record(self, doc: dict[str, Any]) -> ExecutionRecord:
        created_at = doc.get("created_at")
        updated_at = doc.get("updated_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        if not isinstance(updated_at, datetime):
            updated_at = created_at
        next_execution_at = doc.get("next_execution_at")
        if next_execution_at is not None and not isinstance(next_execution_at, datetime):
            next_execution_at = None
        return ExecutionRecord(
            id=str(doc.get("_id", "")),
            workflow_id=str(doc["workflow_id"]),
            lead_id=str(doc["lead_id"]),
            current_step_id=str(doc["current_step_id"]),
            status=str(doc.get("status") or ExecutionStatus.QUEUED.value),
            workflow_version=int(doc.get("workflow_version") or 1),
            next_execution_at=next_execution_at,
            created_at=created_at,
            updated_at=updated_at,
        )

    async def create(
        self,
        *,
        workflow_id: str,
        lead_id: str,
        current_step_id: str,
        workflow_version: int,
        status: str = ExecutionStatus.QUEUED.value,
        next_execution_at: datetime | None = None,
    ) -> ExecutionRecord:
        now = datetime.now(UTC)
        execution_id = str(uuid4())
        doc: dict[str, Any] = {
            "_id": execution_id,
            "workflow_id": workflow_id,
            "lead_id": lead_id,
            "current_step_id": current_step_id,
            "status": status,
            "workflow_version": workflow_version,
            "next_execution_at": next_execution_at,
            "created_at": now,
            "updated_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return self._doc_to_record(doc)

    async def find_by_workflow_and_lead(
        self,
        workflow_id: str,
        lead_id: str,
    ) -> ExecutionRecord | None:
        doc = await get_database()[self.COLLECTION].find_one(
            {"workflow_id": workflow_id, "lead_id": lead_id},
        )
        if doc is None:
            return None
        return self._doc_to_record(doc)

    async def count_for_workflow(self, workflow_id: str) -> int:
        return await get_database()[self.COLLECTION].count_documents(
            {"workflow_id": workflow_id},
        )


execution_repository = ExecutionRepository()
