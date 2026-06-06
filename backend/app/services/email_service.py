import re

from fastapi import HTTPException, status

from app.providers.email.base import EmailProvider, EmailProviderError
from app.providers.email.resend_provider import get_resend_provider
from app.repositories.analytics_repository import analytics_repository
from app.repositories.conversation_repository import conversation_repository
from app.repositories.email_message_repository import email_message_repository
from app.repositories.lead_repository import lead_repository
from app.repositories.workflow_repository import workflow_repository
from app.schemas.email import EmailBodyVersion, GeneratedEmailContent
from app.schemas.email_message import SendEmailResult
from app.schemas.enums import LeadStatus
from app.schemas.requests import EmailSendStatusData
from app.services.analytics_service import AnalyticsService, analytics_service

_EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class EmailService:
    def __init__(
        self,
        email_provider: EmailProvider | None = None,
        analytics: AnalyticsService | None = None,
    ) -> None:
        self._email_provider = email_provider
        self._message_repository = email_message_repository
        self._analytics_service = analytics or analytics_service

    def _provider(self) -> EmailProvider:
        if self._email_provider is not None:
            return self._email_provider
        return get_resend_provider()

    @staticmethod
    def validate_recipients(recipients: list[str]) -> list[str]:
        valid: list[str] = []
        seen: set[str] = set()
        for raw in recipients:
            email = raw.strip()
            if not email:
                continue
            if not _EMAIL_REGEX.match(email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid recipient email: {email}",
                )
            lowered = email.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            valid.append(email)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one valid recipient is required",
            )
        return valid

    @staticmethod
    def _extract_recipients(workflow_definition: dict[str, object]) -> list[str]:
        recipient_emails = workflow_definition.get("recipient_emails")
        if isinstance(recipient_emails, list):
            return [
                str(item).strip()
                for item in recipient_emails
                if isinstance(item, str) and item.strip()
            ]

        recipients = workflow_definition.get("recipients")
        if not isinstance(recipients, list):
            return []

        emails: list[str] = []
        for item in recipients:
            if isinstance(item, str) and item.strip():
                emails.append(item.strip())
            elif isinstance(item, dict):
                email = item.get("email")
                if isinstance(email, str) and email.strip():
                    emails.append(email.strip())
        return emails

    @staticmethod
    def _email_body_from_step(step: dict[str, object]) -> EmailBodyVersion | None:
        raw_email = step.get("email")
        if not isinstance(raw_email, dict):
            return None
        try:
            parsed = GeneratedEmailContent.model_validate(raw_email)
            return parsed.final_user_version
        except Exception:
            subject = raw_email.get("subject")
            html = raw_email.get("html_content")
            plain = raw_email.get("plain_text_content")
            if not all(isinstance(v, str) and v.strip() for v in (subject, html, plain)):
                return None
            return EmailBodyVersion(
                subject=str(subject).strip(),
                html_content=str(html).strip(),
                plain_text_content=str(plain).strip(),
            )

    @staticmethod
    def _first_send_email_step(
        workflow_definition: dict[str, object],
    ) -> tuple[str, EmailBodyVersion] | None:
        steps = workflow_definition.get("steps")
        if not isinstance(steps, list):
            return None
        for step in steps:
            if not isinstance(step, dict):
                continue
            if step.get("type") != "send_email":
                continue
            step_id = step.get("id")
            body = EmailService._email_body_from_step(step)
            if not isinstance(step_id, str) or body is None:
                continue
            return step_id, body
        return None

    async def _load_workflow_definition(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> dict[str, object]:
        record = await workflow_repository.get_by_id(user_id, workflow_id)
        if record is not None and isinstance(record.workflow_definition, dict):
            return record.workflow_definition

        state = await conversation_repository.get_conversation_state(user_id, workflow_id)
        if state is not None:
            raw_workflow = state.get("workflow")
            if isinstance(raw_workflow, dict):
                return raw_workflow

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    async def send_email(
        self,
        *,
        workflow_id: str,
        lead_id: str,
        subject: str,
        html_content: str,
        plain_text_content: str,
        step_id: str | None = None,
    ) -> SendEmailResult:
        recipient = lead_id.strip()
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lead email is required",
            )
        self.validate_recipients([recipient])

        try:
            provider = self._provider()
            message_id = await provider.send_email(
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text_content,
                recipients=[recipient],
                tags={
                    "workflow_id": workflow_id,
                    "lead_id": recipient.lower(),
                },
            )
        except EmailProviderError as exc:
            await self._message_repository.create_failed(
                workflow_id=workflow_id,
                lead_id=recipient.lower(),
                step_id=step_id,
            )
            await self._analytics_service.record_failed(workflow_id)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        await self._message_repository.create_sent(
            resend_message_id=message_id,
            workflow_id=workflow_id,
            lead_id=recipient.lower(),
            step_id=step_id,
        )
        await self._analytics_service.record_sent(workflow_id)
        await lead_repository.upsert_for_workflow(
            workflow_id=workflow_id,
            email=recipient,
            status=LeadStatus.EMAIL_SENT,
        )

        return SendEmailResult(
            resend_message_id=message_id,
            workflow_id=workflow_id,
            lead_id=recipient.lower(),
            step_id=step_id,
        )

    async def record_delivery_event(
        self,
        *,
        resend_message_id: str,
        event_type: str,
    ) -> None:
        record = await self._message_repository.get_by_resend_message_id(resend_message_id)
        if record is None:
            return

        await self._message_repository.apply_tracking_event(
            resend_message_id,
            event=event_type,
        )

        lead_status_map = {
            "delivered": None,
            "opened": LeadStatus.OPENED,
            "clicked": LeadStatus.CLICKED,
            "replied": LeadStatus.REPLIED,
            "failed": None,
            "bounced": None,
        }
        lead_status = lead_status_map.get(event_type)
        if lead_status is not None:
            await lead_repository.update_status_for_event(
                workflow_id=record.workflow_id,
                email=record.lead_id,
                status=lead_status,
            )

    async def send_workflow_email(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> EmailSendStatusData:
        workflow_definition = await self._load_workflow_definition(
            user_id=user_id,
            workflow_id=workflow_id,
        )

        send_step = self._first_send_email_step(workflow_definition)
        if send_step is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow has no send_email step with email content",
            )
        step_id, body = send_step

        raw_recipients = self._extract_recipients(workflow_definition)
        if not raw_recipients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow has no recipients",
            )

        message_ids: list[str] = []
        for recipient in recipients:
            result = await self.send_email(
                workflow_id=workflow_id,
                lead_id=recipient,
                subject=body.subject,
                html_content=body.html_content,
                plain_text_content=body.plain_text_content,
                step_id=step_id,
            )
            message_ids.append(result.resend_message_id)

        first_id = bulk.message_ids[0] if bulk.message_ids else None
        return EmailSendStatusData(
            status="sent",
            message_id=message_ids[0] if message_ids else None,
            recipient_count=len(recipients),
            step_id=step_id,
        )


email_service = EmailService()
