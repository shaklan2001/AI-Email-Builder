"""Immutable workflow definition snapshots created at activation."""

from __future__ import annotations

from app.models.workflow_version import WorkflowVersion
from app.schemas.workflow import WorkflowDefinition
from app.services.workflow_structure import normalize_for_execution


class WorkflowVersionService:
    async def create_snapshot(
        self,
        *,
        workflow_id: str,
        workflow_raw: dict[str, object],
    ) -> WorkflowVersion:
        definition = normalize_for_execution(WorkflowDefinition.model_validate(workflow_raw))
        latest = (
            await WorkflowVersion.find(WorkflowVersion.workflow_id == workflow_id)
            .sort(-WorkflowVersion.version)
            .first_or_none()
        )
        next_version = (latest.version + 1) if latest is not None else 1
        version_doc = WorkflowVersion(
            workflow_id=workflow_id,
            version=next_version,
            definition=definition,
        )
        await version_doc.insert()
        return version_doc

    async def get_definition_dict(
        self,
        *,
        workflow_id: str,
        version: int,
    ) -> dict[str, object] | None:
        doc = (
            await WorkflowVersion.find(
                WorkflowVersion.workflow_id == workflow_id,
                WorkflowVersion.version == version,
            )
            .first_or_none()
        )
        if doc is None:
            return None
        return doc.definition.model_dump(mode="json")


workflow_version_service = WorkflowVersionService()
