"""Process inbound replies: webhook payload → MongoDB → LangGraph → lead update."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.langgraph.reply_graph import get_reply_handling_graph
from app.langgraph.reply_state import ReplyHandlingState
from app.repositories.conversation_repository import conversation_repository
from app.repositories.conversation_thread_repository import (
    ConversationThreadRepository,
    conversation_thread_repository,
)
from app.repositories.inbound_reply_repository import (
    InboundReplyRepository,
    inbound_reply_repository,
)
from app.repositories.lead_repository import LeadRepository, lead_repository
from app.schemas.agent_tool import AgentToolName
from app.schemas.enums import LeadStatus, ThreadMessageKind, ThreadMessageRole, normalize_lead_status
from app.schemas.reply_intent import ReplyIntent
from app.services.agent_tools_service import AgentToolsService, agent_tools_service
from app.services.email_service import EmailService, email_service
from app.services.reply_text import normalize_prospect_reply


@dataclass
class ReplyHandlingResult:
    workflow_id: str
    lead_email: str
    reply_intent: ReplyIntent
    lead_status: LeadStatus
    lead_updated: bool
    reply_stored: bool
    tool_called: bool = False
    selected_tool: AgentToolName | None = None
    tool_result: dict[str, Any] | None = None
    agent_response: str | None = None
    auto_response_sent: bool = False
    human_review_required: bool = False


_REPLY_BODY_KEYS: tuple[str, ...] = ("text", "body", "plain_text", "html", "snippet")


def webhook_has_reply_body(data: dict[str, object]) -> bool:
    """True when the Resend webhook payload already includes message content."""
    return any(
        isinstance(data.get(key), str) and str(data.get(key)).strip()
        for key in _REPLY_BODY_KEYS
    )


def extract_reply_text(data: dict[str, object]) -> str:
    """Extract message body from webhook payload — never use subject as body."""
    parts: list[str] = []
    for key in _REPLY_BODY_KEYS:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    return "\n\n".join(parts)


def extract_reply_subject(data: dict[str, object]) -> str | None:
    subject = data.get("subject")
    if isinstance(subject, str) and subject.strip():
        return subject.strip()
    return None


class ReplyHandlingService:
    def __init__(
        self,
        *,
        leads: LeadRepository | None = None,
        inbound_replies: InboundReplyRepository | None = None,
        agent_tools: AgentToolsService | None = None,
        email: EmailService | None = None,
        threads: ConversationThreadRepository | None = None,
    ) -> None:
        self._leads = leads or lead_repository
        self._inbound_replies = inbound_replies or inbound_reply_repository
        self._agent_tools = agent_tools or agent_tools_service
        self._email = email or email_service
        self._threads = threads or conversation_thread_repository

    async def _product_context(self, *, user_id: str, workflow_id: str) -> str | None:
        state = await conversation_repository.get_conversation_state(user_id, workflow_id)
        if state is None:
            return None
        product = state.get("product_info")
        if isinstance(product, str) and product.strip():
            return product.strip()
        return None

    async def process_inbound_reply(
        self,
        *,
        user_id: str,
        workflow_id: str,
        lead_email: str,
        reply_body: str,
        reply_subject: str | None = None,
        webhook_event_id: str | None = None,
    ) -> ReplyHandlingResult:
        campaign_id = workflow_id
        normalized_reply = normalize_prospect_reply(
            reply_body,
            subject=reply_subject,
        )
        product_context = await self._product_context(
            user_id=user_id,
            workflow_id=workflow_id,
        )

        await self._threads.append_message(
            campaign_id=campaign_id,
            workflow_id=workflow_id,
            lead_email=lead_email,
            role=ThreadMessageRole.PROSPECT,
            message_kind=ThreadMessageKind.PROSPECT_REPLY,
            content=normalized_reply or reply_body,
        )

        graph_state: ReplyHandlingState = {
            "workflow_id": workflow_id,
            "lead_email": lead_email.lower(),
            "reply_body": normalized_reply or reply_body,
            "reply_subject": reply_subject,
            "webhook_event_id": webhook_event_id,
            "product_context": product_context,
        }
        graph = get_reply_handling_graph()
        result_state = await graph.ainvoke(graph_state)

        raw_intent = str(result_state.get("reply_intent") or ReplyIntent.UNKNOWN.value)
        try:
            intent = ReplyIntent(raw_intent)
        except ValueError:
            intent = ReplyIntent.UNKNOWN

        lead_status = normalize_lead_status(
            str(result_state.get("lead_status") or LeadStatus.REPLIED.value),
        )

        stored_reply_body = normalized_reply or reply_body

        inbound = await self._inbound_replies.create(
            workflow_id=workflow_id,
            lead_email=lead_email,
            reply_intent=intent,
            reply_body=stored_reply_body,
            reply_subject=reply_subject,
            webhook_event_id=webhook_event_id,
        )

        human_review_required = await self._threads.is_human_review_required(
            campaign_id=campaign_id,
            lead_email=lead_email,
        )

        tools_run = await self._agent_tools.run_for_prospect_message(
            user_id=user_id,
            workflow_id=workflow_id,
            lead_email=lead_email,
            prospect_message=stored_reply_body,
            inbound_reply_id=inbound.id,
            reply_intent=intent,
        )

        await self._leads.upsert_for_workflow(
            workflow_id=workflow_id,
            email=lead_email,
            status=lead_status,
            reply_intent=intent,
            last_reply_body=stored_reply_body,
            human_review_required=human_review_required,
        )

        auto_response_sent = False
        agent_response = tools_run.agent_response or ""
        if not human_review_required and agent_response.strip():
            auto_response_sent = await self._send_auto_response(
                workflow_id=workflow_id,
                lead_email=lead_email,
                reply_subject=reply_subject,
                body=agent_response,
            )
            if auto_response_sent:
                await self._threads.append_message(
                    campaign_id=campaign_id,
                    workflow_id=workflow_id,
                    lead_email=lead_email,
                    role=ThreadMessageRole.AGENT,
                    message_kind=ThreadMessageKind.AGENT_RESPONSE,
                    content=agent_response.strip(),
                )
                _, human_review_required = await self._threads.increment_auto_reply_count(
                    campaign_id=campaign_id,
                    lead_email=lead_email,
                )
                await self._leads.upsert_for_workflow(
                    workflow_id=workflow_id,
                    email=lead_email,
                    status=lead_status,
                    reply_intent=intent,
                    increment_auto_reply=True,
                    human_review_required=human_review_required,
                )

        return ReplyHandlingResult(
            workflow_id=workflow_id,
            lead_email=lead_email.lower(),
            reply_intent=intent,
            lead_status=lead_status,
            lead_updated=True,
            reply_stored=True,
            tool_called=tools_run.tool_called,
            selected_tool=tools_run.selected_tool,
            tool_result=tools_run.tool_result or None,
            agent_response=agent_response or None,
            auto_response_sent=auto_response_sent,
            human_review_required=human_review_required,
        )

    async def _send_auto_response(
        self,
        *,
        workflow_id: str,
        lead_email: str,
        reply_subject: str | None,
        body: str,
    ) -> bool:
        text = body.strip()
        if not text:
            return False
        subject = f"Re: {reply_subject}" if reply_subject else "Re: Your message"
        html = f"<p>{text.replace(chr(10), '<br>')}</p>"
        await self._email.send_email(
            workflow_id=workflow_id,
            lead_id=lead_email,
            subject=subject,
            html_content=html,
            plain_text_content=text,
            step_id="ai_reply_agent",
        )
        return True


reply_handling_service = ReplyHandlingService()
