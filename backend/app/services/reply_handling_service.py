"""Process inbound replies: webhook payload → MongoDB → LangGraph → lead update."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.langgraph.reply_graph import get_reply_handling_graph
from app.langgraph.reply_state import ReplyHandlingState
from app.repositories.conversation_repository import conversation_repository
from app.repositories.inbound_reply_repository import (
    InboundReplyRepository,
    inbound_reply_repository,
)
from app.repositories.lead_repository import LeadRepository, lead_repository
from app.schemas.agent_tool import AgentToolName
from app.schemas.enums import LeadStatus
from app.schemas.reply_intent import ReplyIntent
from app.services.agent_tools_service import AgentToolsService, agent_tools_service
from app.services.email_service import EmailService, email_service


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


def extract_reply_text(data: dict[str, object]) -> str:
    parts: list[str] = []
    for key in ("text", "body", "plain_text", "html", "snippet"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    subject = data.get("subject")
    if isinstance(subject, str) and subject.strip():
        parts.insert(0, subject.strip())
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
    ) -> None:
        self._leads = leads or lead_repository
        self._inbound_replies = inbound_replies or inbound_reply_repository
        self._agent_tools = agent_tools or agent_tools_service
        self._email = email or email_service

    async def _product_context(self, *, user_id: str, workflow_id: str) -> str | None:
        state = await conversation_repository.get_campaign_state(user_id, workflow_id)
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
        product_context = await self._product_context(
            user_id=user_id,
            workflow_id=workflow_id,
        )

        graph_state: ReplyHandlingState = {
            "workflow_id": workflow_id,
            "lead_email": lead_email.lower(),
            "reply_body": reply_body,
            "reply_subject": reply_subject,
            "webhook_event_id": webhook_event_id,
            "product_context": product_context,
        }
        graph = get_reply_handling_graph()
        result_state = await graph.ainvoke(graph_state)

        intent = ReplyIntent(str(result_state.get("reply_intent") or ReplyIntent.NEED_MORE_INFO.value))
        lead_status = LeadStatus(
            str(result_state.get("lead_status") or LeadStatus.REPLIED.value),
        )

        inbound = await self._inbound_replies.create(
            workflow_id=workflow_id,
            lead_email=lead_email,
            reply_intent=intent,
            reply_body=reply_body,
            reply_subject=reply_subject,
            webhook_event_id=webhook_event_id,
        )

        tools_run = await self._agent_tools.run_for_prospect_message(
            user_id=user_id,
            workflow_id=workflow_id,
            lead_email=lead_email,
            prospect_message=reply_body,
            inbound_reply_id=inbound.id,
        )

        await self._leads.upsert_for_workflow(
            workflow_id=workflow_id,
            email=lead_email,
            status=lead_status,
            reply_intent=intent,
            last_reply_body=reply_body,
        )

        auto_response_sent = await self._send_auto_response(
            workflow_id=workflow_id,
            lead_email=lead_email,
            reply_subject=reply_subject,
            body=tools_run.agent_response or "",
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
            agent_response=tools_run.agent_response or None,
            auto_response_sent=auto_response_sent,
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
