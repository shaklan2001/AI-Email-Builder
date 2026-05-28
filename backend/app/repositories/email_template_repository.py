"""Persist generated email content in MongoDB (email_templates collection)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core.database import get_database


class EmailTemplateRepository:
    COLLECTION = "email_templates"

    async def upsert_latest(
        self,
        *,
        workflow_id: str,
        step_id: str,
        subject: str,
        html_content: str,
        plain_text_content: str,
    ) -> None:
        """Insert a new version for this workflow step (monotonic version per step)."""
        now = datetime.now(UTC)
        collection = get_database()[self.COLLECTION]
        latest = await collection.find_one(
            {"workflow_id": workflow_id, "step_id": step_id},
            sort=[("version", -1)],
        )
        next_version = 1
        if latest is not None and isinstance(latest.get("version"), int):
            next_version = latest["version"] + 1

        doc: dict[str, Any] = {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "version": next_version,
            "subject": subject.strip(),
            "html_content": html_content.strip(),
            "plain_text_content": plain_text_content.strip(),
            "created_at": now,
        }
        await collection.insert_one(doc)

    async def sync_from_workflow(
        self,
        *,
        workflow_id: str,
        templates: list[dict[str, object]],
    ) -> None:
        for item in templates:
            step_id = item.get("step_id")
            subject = item.get("subject")
            html = item.get("html_content")
            plain = item.get("plain_text_content")
            if not all(
                isinstance(v, str) and v.strip()
                for v in (step_id, subject, html, plain)
            ):
                continue
            await self.upsert_latest(
                workflow_id=workflow_id,
                step_id=str(step_id).strip(),
                subject=str(subject).strip(),
                html_content=str(html).strip(),
                plain_text_content=str(plain).strip(),
            )

    async def list_latest_for_workflow(self, workflow_id: str) -> list[dict[str, Any]]:
        collection = get_database()[self.COLLECTION]
        cursor = collection.find({"workflow_id": workflow_id}).sort(
            [("step_id", 1), ("version", -1)],
        )
        seen: set[str] = set()
        results: list[dict[str, Any]] = []
        async for doc in cursor:
            step_id = str(doc.get("step_id", ""))
            if not step_id or step_id in seen:
                continue
            seen.add(step_id)
            results.append(doc)
        return results


email_template_repository = EmailTemplateRepository()
