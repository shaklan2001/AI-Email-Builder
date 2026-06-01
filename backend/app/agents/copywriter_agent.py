import json
import re

from app.providers.llm.base import LLMProvider, LLMProviderError
from app.providers.llm.groq_provider import get_groq_provider
from app.schemas.campaign import CampaignData
from app.schemas.email import GeneratedEmailContent
from app.schemas.workflow import WorkflowDefinition, WorkflowStep

_COPYWRITER_SYSTEM = """You are a professional B2B sales copywriter writing outbound email campaigns.
Use the campaign details and the email step purpose to write compelling, professional sales email content.

Return ONLY valid JSON with this exact shape:
{
  "subject": "...",
  "html_content": "...",
  "plain_text_content": "..."
}

Rules:
- Subject: concise, specific, professional (no ALL CAPS spam).
- html_content: complete HTML email body (use simple structure: <p>, <a> for CTA; inline styles optional).
- plain_text_content: same message as plain text (no HTML tags).
- Sales-focused, clear value prop, one primary CTA aligned with campaign.
- Do not invent fake statistics or guarantees.
- Keep length appropriate for the step (initial outreach vs follow-up)."""


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


def _validate_email_payload(raw: dict[str, object]) -> GeneratedEmailContent | None:
    subject = raw.get("subject")
    html = raw.get("html_content")
    plain = raw.get("plain_text_content")
    if not all(isinstance(v, str) and v.strip() for v in (subject, html, plain)):
        return None
    try:
        return GeneratedEmailContent.from_ai_draft(
            subject=str(subject).strip(),
            html_content=str(html).strip(),
            plain_text_content=str(plain).strip(),
        )
    except Exception:
        return None


class CopywriterAgent:
    """Generates subject, HTML, and plain text for workflow email steps."""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        return get_groq_provider()

    async def generate_email_for_step(
        self,
        *,
        campaign: CampaignData,
        step: WorkflowStep,
        step_index: int,
        total_email_steps: int,
    ) -> GeneratedEmailContent:
        purpose = step.name or "Send Email"
        branch_note = f" (branch: {step.branch})" if step.branch else ""
        user_prompt = (
            f"{campaign.authoritative_summary()}\n\n"
            f"Email step {step_index + 1} of {total_email_steps}{branch_note}\n"
            f"Step purpose: {purpose}\n"
            f"Step id: {step.id}\n\n"
            "Write the email for this step using ONLY the campaign brief above."
        )

        llm = self._get_llm()
        try:
            raw_text = await llm.generate(_COPYWRITER_SYSTEM, user_prompt)
        except LLMProviderError as exc:
            raise exc

        content = _validate_email_payload(_parse_json_object(raw_text))
        if content is None:
            raise LLMProviderError("Email generation returned invalid content")

        return content

    async def generate_emails_for_workflow(
        self,
        campaign: CampaignData,
        definition: WorkflowDefinition,
    ) -> WorkflowDefinition:
        email_steps = [s for s in definition.steps if s.type == "send_email"]
        if not email_steps:
            return definition

        updated_steps: list[WorkflowStep] = []
        email_index = 0
        for step in definition.steps:
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
                step_index=email_index,
                total_email_steps=len(email_steps),
            )
            email_index += 1
            updated_steps.append(
                step.model_copy(update={"email": content}),
            )

        return WorkflowDefinition(
            workflow_type=definition.workflow_type,
            steps=updated_steps,
        )


copywriter_agent = CopywriterAgent()
