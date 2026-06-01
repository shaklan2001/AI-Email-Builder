from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException, status

from app.repositories.conversation_repository import conversation_repository
from app.repositories.workflow_repository import workflow_repository
from app.services.conversation_state_service import empty_conversation_state, normalize_conversation_state
from app.services.email_service import EmailService
from app.services.persistence import save_conversation_state

_EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _normalize_email(raw: str) -> str | None:
    email = raw.strip()
    if not email or not _EMAIL_REGEX.match(email):
        return None
    return email


def _recipient_dicts_from_emails(emails: list[str]) -> list[dict[str, str]]:
    return [{"email": email} for email in emails]


def _emails_from_state_recipients(stored: object) -> list[str]:
    if not isinstance(stored, list):
        return []
    emails: list[str] = []
    for item in stored:
        if isinstance(item, str) and item.strip():
            emails.append(item.strip())
        elif isinstance(item, dict):
            email = item.get("email")
            if isinstance(email, str) and email.strip():
                emails.append(email.strip())
    return emails


def _merge_recipient_emails(existing: list[str], incoming: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for raw in [*existing, *incoming]:
        email = _normalize_email(raw)
        if email is None:
            continue
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(email)
    return merged


def _apply_recipients_to_workflow(
    workflow: dict[str, Any] | None,
    emails: list[str],
) -> dict[str, Any] | None:
    if workflow is None:
        return None
    updated = dict(workflow)
    updated["recipient_emails"] = emails
    updated["recipients"] = _recipient_dicts_from_emails(emails)
    return updated


class RecipientService:
    async def list_recipients(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> dict[str, object]:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        emails: list[str] = []
        if isinstance(record.workflow_definition, dict):
            emails = EmailService._extract_recipients(record.workflow_definition)

        state = await conversation_repository.get_conversation_state(user_id, workflow_id)
        if not emails and state is not None:
            emails = _emails_from_state_recipients(state.get("recipients"))
            workflow_raw = state.get("workflow")
            if not emails and isinstance(workflow_raw, dict):
                emails = EmailService._extract_recipients(workflow_raw)

        return {
            "recipients": _recipient_dicts_from_emails(emails),
            "valid_count": len(emails),
            "invalid_count": 0,
        }

    async def add_recipients(
        self,
        *,
        user_id: str,
        workflow_id: str,
        emails: list[str],
    ) -> dict[str, object]:
        if not emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one email is required",
            )

        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        invalid_rows: list[dict[str, str]] = []
        candidates: list[str] = []
        for index, raw in enumerate(emails, start=1):
            if not isinstance(raw, str):
                invalid_rows.append(
                    {"row": str(index), "email": "", "reason": "Invalid email format"},
                )
                continue
            normalized = _normalize_email(raw)
            if normalized is None:
                invalid_rows.append(
                    {
                        "row": str(index),
                        "email": raw.strip(),
                        "reason": "Invalid email format",
                    },
                )
                continue
            candidates.append(normalized)

        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid emails to add",
            )

        state = await conversation_repository.get_conversation_state(user_id, workflow_id)
        if state is None:
            state = empty_conversation_state(user_id=user_id, workflow_id=workflow_id)

        existing = _emails_from_state_recipients(state.get("recipients"))
        if isinstance(record.workflow_definition, dict):
            existing = _merge_recipient_emails(
                existing,
                EmailService._extract_recipients(record.workflow_definition),
            )

        merged = _merge_recipient_emails(existing, candidates)
        EmailService.validate_recipients(merged)

        state["recipients"] = _recipient_dicts_from_emails(merged)  # type: ignore[typeddict-item]
        workflow_raw = state.get("workflow")
        if isinstance(workflow_raw, dict):
            state["workflow"] = _apply_recipients_to_workflow(workflow_raw, merged)

        normalized = await save_conversation_state(user_id, workflow_id, state)

        if isinstance(record.workflow_definition, dict):
            wf = _apply_recipients_to_workflow(record.workflow_definition, merged)
            if wf is not None:
                await workflow_repository.upsert_workflow_definition(
                    user_id=user_id,
                    workflow_id=workflow_id,
                    workflow_definition=wf,
                )
        elif isinstance(normalized.get("workflow"), dict):
            await workflow_repository.upsert_workflow_definition(
                user_id=user_id,
                workflow_id=workflow_id,
                workflow_definition=normalized["workflow"],  # type: ignore[arg-type]
            )

        return {
            "valid_count": len(merged),
            "invalid_count": len(invalid_rows),
            "valid_emails": merged,
            "invalid_rows": invalid_rows,
            "recipients": _recipient_dicts_from_emails(merged),
        }


recipient_service = RecipientService()
