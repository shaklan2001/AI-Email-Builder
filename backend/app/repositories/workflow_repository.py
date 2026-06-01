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
    active_version: int | None = None
    activated_at: datetime | None = None
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
        active_version = doc.get("active_version")
        if active_version is not None:
            active_version = int(active_version)
        activated_at = doc.get("activated_at")
        if not isinstance(activated_at, datetime):
            activated_at = None
        return WorkflowRecord(
            id=workflow_id,
            user_id=str(doc["user_id"]),
            name=str(doc.get("name") or "Untitled Workflow"),
            status=str(doc.get("status") or "draft"),
            workflow_definition=doc.get("workflow_definition")
            if isinstance(doc.get("workflow_definition"), dict)
            else None,
            active_version=active_version,
            activated_at=activated_at,
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

    async def list_by_user_id(self, user_id: str) -> list[WorkflowRecord]:
        cursor = get_database()[self.COLLECTION].find({"user_id": user_id}).sort(
            "created_at",
            -1,
        )
        docs = await cursor.to_list(length=None)
        return [self._doc_to_record(doc) for doc in docs]

    async def get_by_id(self, user_id: str, workflow_id: str) -> WorkflowRecord | None:
        doc = await get_database()[self.COLLECTION].find_one(
            {"_id": workflow_id, "user_id": user_id},
        )
        if doc is None:
            return None
        return self._doc_to_record(doc)

    async def get_by_id_only(self, workflow_id: str) -> WorkflowRecord | None:
        doc = await get_database()[self.COLLECTION].find_one({"_id": workflow_id})
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

    async def clear_workflow_definition(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> None:
        now = datetime.now(UTC)
        await get_database()[self.COLLECTION].update_one(
            {"_id": workflow_id, "user_id": user_id},
            {
                "$set": {
                    "workflow_definition": None,
                    "updated_at": now,
                },
            },
        )

    async def delete(self, *, user_id: str, workflow_id: str) -> None:
        await get_database()[self.COLLECTION].delete_one(
            {"_id": workflow_id, "user_id": user_id},
        )

    async def update_status(
        self,
        *,
        user_id: str,
        workflow_id: str,
        status: str,
    ) -> WorkflowRecord | None:
        now = datetime.now(UTC)
        result = await get_database()[self.COLLECTION].find_one_and_update(
            {"_id": workflow_id, "user_id": user_id},
            {"$set": {"status": status, "updated_at": now}},
            return_document=True,
        )
        if result is None:
            return None
        return self._doc_to_record(result)

    async def activate(
        self,
        *,
        user_id: str,
        workflow_id: str,
        active_version: int,
        workflow_definition: dict[str, Any],
        activated_at: datetime,
    ) -> WorkflowRecord | None:
        now = datetime.now(UTC)
        result = await get_database()[self.COLLECTION].find_one_and_update(
            {"_id": workflow_id, "user_id": user_id},
            {
                "$set": {
                    "status": "active",
                    "active_version": active_version,
                    "workflow_definition": workflow_definition,
                    "activated_at": activated_at,
                    "updated_at": now,
                },
            },
            return_document=True,
        )
        if result is None:
            return None
        return self._doc_to_record(result)


workflow_repository = WorkflowRepository()
