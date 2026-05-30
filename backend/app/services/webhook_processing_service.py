import json
import re
from datetime import UTC, datetime
from email.utils import parseaddr

from fastapi import HTTPException, status
from pydantic import BaseModel
from svix.webhooks import Webhook, WebhookVerificationError

from app.core.config import settings
from app.core.logger import get_logger
from app.models.webhook_event import WebhookEventType
from app.repositories.webhook_event_repository import WebhookEventRepository, webhook_event_repository
from app.repositories.workflow_repository import WorkflowRepository, workflow_repository
from app.repositories.workflow_run_repository import WorkflowRunRepository, workflow_run_repository
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.analytics_service import AnalyticsService, analytics_service
from app.services.email_service import EmailService, email_service
from app.providers.email.resend_inbound import fetch_received_email_text
from app.services.reply_handling_service import (
    ReplyHandlingService,
    extract_reply_subject,
    extract_reply_text,
    reply_handling_service,
    webhook_has_reply_body,
)
from app.services.reply_text import normalize_prospect_reply
from app.services.workflow_execution_service import WorkflowExecutionService, workflow_execution_service
from app.workers.dispatch import dispatch_after_step

logger = get_logger(__name__)

RESEND_EVENT_TYPE_MAP: dict[str, WebhookEventType] = {
    "email.delivered": "delivered",
    "email.opened": "opened",
    "email.clicked": "clicked",
    "email.received": "replied",
    "email.bounced": "bounced",
}


class WebhookProcessResult(BaseModel):
    status: str
    event_type: str | None = None
    duplicate: bool = False
    workflow_updated: bool = False
    reply_classified: bool = False
    reply_intent: str | None = None
    lead_updated: bool = False
    tool_called: bool = False
    selected_tool: str | None = None
    agent_response: str | None = None


class WebhookProcessingService:
    def __init__(
        self,
        *,
        event_repository: WebhookEventRepository | None = None,
        run_repository: WorkflowRunRepository | None = None,
        workflow_repo: WorkflowRepository | None = None,
        execution_service: WorkflowExecutionService | None = None,
        analytics: AnalyticsService | None = None,
        email: EmailService | None = None,
        reply_handler: ReplyHandlingService | None = None,
    ) -> None:
        self._event_repository = event_repository or webhook_event_repository
        self._run_repository = run_repository or workflow_run_repository
        self._workflow_repository = workflow_repo or workflow_repository
        self._execution_service = execution_service or workflow_execution_service
        self._analytics_service = analytics or analytics_service
        self._email_service = email or email_service
        self._reply_handler = reply_handler or reply_handling_service

    def verify_signature(self, *, payload: bytes, headers: dict[str, str]) -> dict[str, object]:
        secret = settings.resend_webhook_secret.strip()
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RESEND_WEBHOOK_SECRET is not configured",
            )

        svix_headers = {
            "svix-id": headers.get("svix-id", ""),
            "svix-timestamp": headers.get("svix-timestamp", ""),
            "svix-signature": headers.get("svix-signature", ""),
        }
        if not all(svix_headers.values()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        try:
            wh = Webhook(secret)
            verified = wh.verify(payload, svix_headers)
        except WebhookVerificationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            ) from exc

        if isinstance(verified, dict):
            return verified
        if isinstance(verified, bytes | str):
            parsed = json.loads(verified)
            if isinstance(parsed, dict):
                return parsed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        )

    @staticmethod
    def _parse_email_address(value: str) -> str | None:
        _, email = parseaddr(value.strip())
        if email and "@" in email:
            return email.lower()
        cleaned = value.strip().lower()
        if "@" in cleaned:
            match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", cleaned)
            if match:
                return match.group(0).lower()
        return None

    @staticmethod
    def _normalize_event_type(resend_type: str) -> WebhookEventType | None:
        return RESEND_EVENT_TYPE_MAP.get(resend_type.strip().lower())

    @staticmethod
    def _parse_timestamp(payload: dict[str, object]) -> datetime:
        created_at = payload.get("created_at")
        if isinstance(created_at, str):
            normalized = created_at.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(normalized)
            except ValueError:
                pass
        return datetime.now(UTC)

    def _extract_recipient_email(
        self,
        *,
        event_type: WebhookEventType,
        data: dict[str, object],
    ) -> str | None:
        if event_type == "replied":
            from_value = data.get("from")
            if isinstance(from_value, str):
                return self._parse_email_address(from_value)
            return None

        to_value = data.get("to")
        if isinstance(to_value, str):
            return self._parse_email_address(to_value)
        if isinstance(to_value, list):
            for item in to_value:
                if isinstance(item, str):
                    parsed = self._parse_email_address(item)
                    if parsed:
                        return parsed
        return None

    async def _load_workflow_definition(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> WorkflowDefinition:
        record = await self._workflow_repository.get_by_id(user_id, workflow_id)
        if record is not None and isinstance(record.workflow_definition, dict):
            return WorkflowDefinition.model_validate(record.workflow_definition)

        from app.repositories.conversation_repository import conversation_repository

        state = await conversation_repository.get_campaign_state(user_id, workflow_id)
        if state is not None:
            raw_workflow = state.get("workflow")
            if isinstance(raw_workflow, dict):
                return WorkflowDefinition.model_validate(raw_workflow)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    @staticmethod
    def _find_step(steps: list[WorkflowStep], step_id: str) -> WorkflowStep | None:
        for step in steps:
            if step.id == step_id:
                return step
        return None

    async def _resolve_active_run(
        self,
        *,
        recipient: str,
        workflow_id_hint: str | None = None,
    ) -> tuple[str, str, str] | None:
        runs = await self._run_repository.find_active_by_recipient(recipient)
        if not runs:
            return None

        candidates = runs
        if workflow_id_hint:
            candidates = [run for run in runs if run.workflow_id == workflow_id_hint]
            if not candidates:
                return None

        for run in candidates:
            workflow = await self._workflow_repository.get_by_id_only(run.workflow_id)
            if workflow is not None:
                return run.id, workflow.user_id, run.workflow_id
        return None

    async def _evaluate_reply_condition(
        self,
        *,
        workflow_run_id: str,
        user_id: str,
    ) -> bool:
        run = await self._run_repository.get_by_id(workflow_run_id)
        if run is None:
            return False

        definition = await self._load_workflow_definition(
            user_id=user_id,
            workflow_id=run.workflow_id,
        )
        current_step = self._find_step(definition.steps, run.current_step)
        if current_step is None:
            return False

        if current_step.type == "wait":
            next_step_id = self._execution_service._next_linear_step_id(
                definition.steps,
                current_step.id,
            )
            if next_step_id is None:
                return False
            now = datetime.now(UTC)
            await self._run_repository.update(
                run.id,
                current_step=next_step_id,
                status="queued",
                next_execution_at=now,
            )
            run = await self._run_repository.get_by_id(workflow_run_id)
            if run is None:
                return False
            current_step = self._find_step(definition.steps, run.current_step)
            if current_step is None:
                return False

        if current_step.type not in ("condition", "reply_condition"):
            return False
        if current_step.type == "condition" and current_step.condition != "reply_received":
            return False

        result = await self._execution_service.execute_step(
            workflow_run_id,
            user_id=user_id,
            condition_result=True,
        )
        dispatch_after_step(user_id=user_id, result=result)
        return True

    async def process(
        self,
        *,
        payload: bytes,
        headers: dict[str, str],
    ) -> WebhookProcessResult:
        event_payload = self.verify_signature(payload=payload, headers=headers)
        event_id = headers.get("svix-id", "").strip()
        if not event_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing webhook event id",
            )

        existing = await self._event_repository.get_by_event_id(event_id)
        if existing is not None:
            logger.info("webhook_duplicate_skipped", event_id=event_id)
            return WebhookProcessResult(
                status="ok",
                event_type=existing.event_type,
                duplicate=True,
                workflow_updated=existing.processed,
            )

        resend_type = str(event_payload.get("type", ""))
        event_type = self._normalize_event_type(resend_type)
        if event_type is None:
            logger.info("webhook_event_ignored", resend_type=resend_type)
            return WebhookProcessResult(status="ok")

        data = event_payload.get("data")
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload",
            )

        recipient = self._extract_recipient_email(event_type=event_type, data=data)
        if recipient is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not resolve recipient from webhook payload",
            )

        workflow_id_hint: str | None = None
        tags = data.get("tags")
        if isinstance(tags, dict):
            tag_workflow_id = tags.get("workflow_id")
            if isinstance(tag_workflow_id, str) and tag_workflow_id.strip():
                workflow_id_hint = tag_workflow_id.strip()
        elif isinstance(tags, list):
            for item in tags:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                value = item.get("value")
                if name == "workflow_id" and isinstance(value, str) and value.strip():
                    workflow_id_hint = value.strip()
                    break

        resolved = await self._resolve_active_run(
            recipient=recipient,
            workflow_id_hint=workflow_id_hint,
        )

        stored_workflow_id = workflow_id_hint
        if stored_workflow_id is None and resolved is not None:
            stored_workflow_id = resolved[2]

        resend_email_id = data.get("email_id")
        if not isinstance(resend_email_id, str):
            resend_email_id = None

        timestamp = self._parse_timestamp(event_payload)
        stored = await self._event_repository.create(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            recipient=recipient,
            workflow_id=stored_workflow_id,
            resend_email_id=resend_email_id,
            payload=event_payload,
        )
        if stored is None:
            logger.info("webhook_duplicate_skipped_on_insert", event_id=event_id)
            return WebhookProcessResult(status="ok", event_type=event_type, duplicate=True)

        if stored_workflow_id:
            await self._analytics_service.record_webhook_event(
                stored_workflow_id,
                event_type,
            )

        if resend_email_id:
            tracking_event = "failed" if event_type == "bounced" else event_type
            await self._email_service.record_delivery_event(
                resend_message_id=resend_email_id,
                event_type=tracking_event,
            )

        workflow_updated = False
        reply_classified = False
        reply_intent_value: str | None = None
        lead_updated = False
        tool_called = False
        selected_tool_value: str | None = None
        agent_response_value: str | None = None

        if event_type == "replied" and stored_workflow_id:
            run_id: str | None = None
            user_id: str | None = None
            if resolved is not None:
                run_id, user_id, _ = resolved

            if user_id is None:
                record = await self._workflow_repository.get_by_id_only(stored_workflow_id)
                if record is not None:
                    user_id = record.user_id

            if user_id:
                reply_subject = extract_reply_subject(data)
                reply_body = extract_reply_text(data)

                # Resend email.received webhooks often omit body text — fetch via API.
                if resend_email_id and not webhook_has_reply_body(data):
                    try:
                        fetched = await fetch_received_email_text(resend_email_id)
                        if fetched:
                            reply_body = fetched
                            logger.info(
                                "reply_body_fetched_from_resend",
                                event_id=event_id,
                                resend_email_id=resend_email_id,
                            )
                        else:
                            logger.warning(
                                "reply_body_fetch_empty",
                                event_id=event_id,
                                resend_email_id=resend_email_id,
                            )
                    except Exception:
                        logger.exception(
                            "reply_body_fetch_failed",
                            event_id=event_id,
                            resend_email_id=resend_email_id,
                        )

                reply_body = normalize_prospect_reply(
                    reply_body,
                    subject=reply_subject,
                )
                try:
                    handling = await self._reply_handler.process_inbound_reply(
                        user_id=user_id,
                        workflow_id=stored_workflow_id,
                        lead_email=recipient,
                        reply_body=reply_body,
                        reply_subject=reply_subject,
                        webhook_event_id=stored.id,
                    )
                    reply_classified = True
                    reply_intent_value = handling.reply_intent.value
                    lead_updated = handling.lead_updated
                    tool_called = handling.tool_called
                    if handling.selected_tool is not None:
                        selected_tool_value = handling.selected_tool.value
                    agent_response_value = handling.agent_response
                except Exception:
                    logger.exception(
                        "reply_handling_failed",
                        event_id=event_id,
                        workflow_id=stored_workflow_id,
                        recipient=recipient,
                    )

            if resolved is not None and run_id and user_id:
                try:
                    workflow_updated = await self._evaluate_reply_condition(
                        workflow_run_id=run_id,
                        user_id=user_id,
                    )
                except HTTPException:
                    logger.exception(
                        "webhook_workflow_update_failed",
                        event_id=event_id,
                        workflow_run_id=run_id,
                    )

            if workflow_updated or reply_classified:
                await self._event_repository.mark_processed(stored.id)

        logger.info(
            "webhook_processed",
            event_id=event_id,
            event_type=event_type,
            recipient=recipient,
            workflow_id=stored_workflow_id,
            workflow_updated=workflow_updated,
            reply_classified=reply_classified,
            reply_intent=reply_intent_value,
            lead_updated=lead_updated,
            tool_called=tool_called,
            selected_tool=selected_tool_value,
        )
        return WebhookProcessResult(
            status="ok",
            event_type=event_type,
            workflow_updated=workflow_updated,
            reply_classified=reply_classified,
            reply_intent=reply_intent_value,
            lead_updated=lead_updated,
            tool_called=tool_called,
            selected_tool=selected_tool_value,
            agent_response=agent_response_value,
        )


webhook_processing_service = WebhookProcessingService()
