"""Production agent: generate promotional, follow-up, and reply campaign emails."""

from __future__ import annotations

import json
import re

from langsmith import traceable

from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.repositories.email_template_repository import email_template_repository
from app.schemas.campaign import CampaignData
from app.schemas.email import GeneratedEmailContent
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.collection_preferences import email_length_instructions
from app.services.email_type import (
    EmailType,
    email_type_label,
    infer_email_type,
    workflow_has_reply_branch,
)
from app.services.conversation_state_service import email_templates_from_workflow

_EMAIL_SYSTEM = """You are a professional B2B sales copywriter writing outbound email campaigns.
Use ONLY the campaign inputs provided. Return ONLY valid JSON:
{
  "subject": "...",
  "html_content": "...",
  "plain_text_content": "..."
}

Rules:
- subject: concise, specific, professional (no ALL CAPS spam).
- html_content: complete HTML body (<p>, <a> for CTA; optional simple inline styles).
  If an image URL is provided, include <img src="..." alt="product" style="max-width:100%;"> once near the top.
  If a website URL is provided, link the CTA to that URL.
- plain_text_content: same message without HTML tags.
- Match the requested email type (promotional, follow-up, or reply).
- Sales-focused, one clear CTA aligned with campaign tone.
- Use the Campaign / Company Name when provided. Never write placeholder text such as
  "Company Name", "Valued Customer", "[Your Company]", or bracketed filler.
- Greet with "Hi there," or reference the product/audience — do not invent a fake person name.
- Do not invent statistics or guarantees."""

_PLACEHOLDER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"dear\s+valued\s+customer", re.IGNORECASE),
    re.compile(r"\bcompany\s+name\b", re.IGNORECASE),
    re.compile(r"\[your\s+company\]", re.IGNORECASE),
    re.compile(r"\[.+?\]"),
)


def _parse_json_object(text: str) -> dict[str, object]:
    cleaned = text.strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
    if fence:
        try:
            parsed = json.loads(fence.group(1).strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    brace = re.search(r"\{[\s\S]*\}", cleaned)
    if brace:
        try:
            parsed = json.loads(brace.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {}


def _contains_placeholder_text(*parts: str) -> bool:
    combined = "\n".join(parts)
    return any(pattern.search(combined) for pattern in _PLACEHOLDER_PATTERNS)


def _validate_email_payload(raw: dict[str, object]) -> GeneratedEmailContent | None:
    subject = raw.get("subject")
    html = raw.get("html_content")
    plain = raw.get("plain_text_content")
    if not all(isinstance(v, str) and v.strip() for v in (subject, html, plain)):
        return None
    subject_s = str(subject).strip()
    html_s = str(html).strip()
    plain_s = str(plain).strip()
    if _contains_placeholder_text(subject_s, html_s, plain_s):
        return None
    try:
        return GeneratedEmailContent.from_ai_draft(
            subject=subject_s,
            html_content=html_s,
            plain_text_content=plain_s,
        )
    except Exception:
        return None


def _type_instructions(email_type: EmailType) -> str:
    if email_type == "promotional":
        return (
            "Email type: PROMOTIONAL (initial outreach).\n"
            "Introduce the product, hook the reader, clear value prop, single primary CTA."
        )
    if email_type == "follow_up":
        return (
            "Email type: FOLLOW-UP (recipient did not reply).\n"
            "Short, polite bump — reference prior outreach, add light urgency, same CTA."
        )
    return (
        "Email type: REPLY (lead showed interest).\n"
        "Warm, helpful response — acknowledge interest, answer implied questions, "
        "guide to next step (demo/booking) using the campaign CTA."
    )


class EmailGenerationAgent:
    """Generates subject, HTML, and plain text for workflow email steps."""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        return get_groq_provider()

    @traceable(run_type="chain", name="email_generation_step")
    async def generate_email_for_step(
        self,
        *,
        campaign: CampaignData,
        step: WorkflowStep,
        steps: list[WorkflowStep],
        step_index: int,
        total_email_steps: int,
        email_type: EmailType | None = None,
        email_length: str | None = None,
        email_length_words: int | None = None,
    ) -> GeneratedEmailContent:
        resolved_type = email_type or infer_email_type(step, steps)
        purpose = step.name or "Send Email"
        branch_note = f" (branch: {step.branch})" if step.branch else ""
        length_note = email_length_instructions(
            email_length,
            words=email_length_words,
        )
        user_prompt = (
            f"{campaign.email_generation_context()}\n\n"
            f"{length_note}\n\n"
            f"{_type_instructions(resolved_type)}\n\n"
            f"Label: {email_type_label(resolved_type)}\n"
            f"Email step {step_index + 1} of {total_email_steps}{branch_note}\n"
            f"Step purpose: {purpose}\n"
            f"Step id: {step.id}\n\n"
            "Write the email using ONLY the campaign inputs above."
        )

        llm = self._get_llm()
        try:
            raw_text = await llm.generate(_EMAIL_SYSTEM, user_prompt)
        except LLMProviderError as exc:
            raise exc

        content = _validate_email_payload(_parse_json_object(raw_text))
        if content is None:
            raise LLMProviderError("Email generation returned invalid content")
        return content

    @traceable(run_type="chain", name="email_generation_reply_template")
    async def generate_reply_template(
        self,
        *,
        campaign: CampaignData,
        steps: list[WorkflowStep],
    ) -> GeneratedEmailContent:
        return await self.generate_email_for_step(
            campaign=campaign,
            step=WorkflowStep(id="reply_agent", type="send_email", name="AI Reply Agent"),
            steps=steps,
            step_index=0,
            total_email_steps=1,
            email_type="reply",
        )

    @traceable(run_type="chain", name="email_generation")
    async def generate_emails_for_workflow(
        self,
        campaign: CampaignData,
        definition: WorkflowDefinition,
        *,
        workflow_id: str | None = None,
        persist: bool = True,
        email_length: str | None = None,
        email_length_words: int | None = None,
    ) -> WorkflowDefinition:
        steps = list(definition.steps)
        email_steps = [s for s in steps if s.type == "send_email"]
        if not email_steps and not workflow_has_reply_branch(steps):
            return definition

        updated_steps: list[WorkflowStep] = []
        email_index = 0
        for step in steps:
            if step.type != "send_email":
                updated_steps.append(step)
                continue

            if step.email is not None and (
                step.email.user_edited or step.email.ai_generated_version is not None
            ):
                updated_steps.append(step)
                email_index += 1
                continue

            content = await self.generate_email_for_step(
                campaign=campaign,
                step=step,
                steps=steps,
                step_index=email_index,
                total_email_steps=len(email_steps),
                email_length=email_length,
                email_length_words=email_length_words,
            )
            email_index += 1
            updated_steps.append(step.model_copy(update={"email": content}))

        result = definition.model_copy(update={"steps": updated_steps})
        reply_content: GeneratedEmailContent | None = None
        if workflow_has_reply_branch(steps):
            reply_content = await self.generate_reply_template(
                campaign=campaign,
                steps=steps,
            )

        if persist and workflow_id:
            await self.persist_workflow_emails(
                workflow_id=workflow_id,
                definition=result,
                reply_content=reply_content,
            )

        return result

    async def persist_workflow_emails(
        self,
        *,
        workflow_id: str,
        definition: WorkflowDefinition,
        reply_content: GeneratedEmailContent | None = None,
    ) -> None:
        workflow_dict = definition.to_api_dict()
        templates = list(email_templates_from_workflow(workflow_dict))
        if reply_content is not None:
            final = reply_content.final_user_version
            templates.append(
                {
                    "step_id": "reply_agent",
                    "subject": final.subject,
                    "html_content": final.html_content,
                    "plain_text_content": final.plain_text_content,
                },
            )
        if templates:
            await email_template_repository.sync_from_workflow(
                workflow_id=workflow_id,
                templates=templates,
            )


email_generation_agent = EmailGenerationAgent()
