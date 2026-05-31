from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.core.database import get_database


class WorkflowRecord(BaseModel):
    id: str
    user_id: str
    name: str
    status: str
    workflow_definition: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class WorkflowRepository:
    COLLECTION = "workflows"

    def _doc_to_record(self, doc: dict[str, Any]) -> WorkflowRecord:
        workflow_id = str(doc.get("_id") or doc.get("workflow_id", ""))
        created_at = doc.get("created_at")
        updated_at = doc.get("updated_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        if not isinstance(updated_at, datetime):
            updated_at = created_at
        return WorkflowRecord(
            id=workflow_id,
            user_id=str(doc["user_id"]),
            name=str(doc.get("name") or "Untitled Workflow"),
            status=str(doc.get("status") or "draft"),
            workflow_definition=doc.get("workflow_definition")
            if isinstance(doc.get("workflow_definition"), dict)
            else None,
            created_at=created_at,
            updated_at=updated_at,
        )

    async def create(
        self,
        *,
        user_id: str,
        workflow_id: str,
        name: str,
        status: str = "draft",
    ) -> WorkflowRecord:
        now = datetime.now(UTC)
        doc: dict[str, Any] = {
            "_id": workflow_id,
            "user_id": user_id,
            "name": name,
            "status": status,
            "workflow_definition": None,
            "created_at": now,
            "updated_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return self._doc_to_record(doc)

    async def get_by_id(self, user_id: str, workflow_id: str) -> WorkflowRecord | None:
        doc = await get_database()[self.COLLECTION].find_one(
            {"_id": workflow_id, "user_id": user_id},
        )
        if doc is None:
            return None
        return self._doc_to_record(doc)

    async def update_name(
        self,
        *,
        user_id: str,
        workflow_id: str,
        name: str,
    ) -> None:
        now = datetime.now(UTC)
        await get_database()[self.COLLECTION].update_one(
            {"_id": workflow_id, "user_id": user_id},
            {"$set": {"name": name.strip(), "updated_at": now}},
        )

    async def upsert_workflow_definition(
        self,
        *,
        user_id: str,
        workflow_id: str,
        workflow_definition: dict[str, Any],
    ) -> None:
        now = datetime.now(UTC)
        await get_database()[self.COLLECTION].update_one(
            {"_id": workflow_id, "user_id": user_id},
            {
                "$set": {
                    "workflow_definition": workflow_definition,
                    "updated_at": now,
                },
            },
        )


workflow_repository = WorkflowRepository()
