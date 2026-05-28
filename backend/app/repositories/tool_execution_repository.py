"""Persist agent tool execution history."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import get_database
from app.schemas.agent_tool import AgentToolName


class ToolExecutionRecord:
    def __init__(
        self,
        *,
        id: str,
        workflow_id: str,
        lead_email: str,
        tool_name: str,
        prospect_message: str,
        result: dict[str, Any],
        agent_response: str,
        inbound_reply_id: str | None,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.workflow_id = workflow_id
        self.lead_email = lead_email
        self.tool_name = tool_name
        self.prospect_message = prospect_message
        self.result = result
        self.agent_response = agent_response
        self.inbound_reply_id = inbound_reply_id
        self.created_at = created_at


class ToolExecutionRepository:
    COLLECTION = "tool_executions"

    def _doc_to_record(self, doc: dict[str, Any]) -> ToolExecutionRecord:
        created_at = doc.get("created_at")
        if not isinstance(created_at, datetime):
            created_at = datetime.now(UTC)
        result = doc.get("result")
        if not isinstance(result, dict):
            result = {}
        return ToolExecutionRecord(
            id=str(doc.get("_id", "")),
            workflow_id=str(doc["workflow_id"]),
            lead_email=str(doc["lead_email"]),
            tool_name=str(doc.get("tool_name") or AgentToolName.NONE.value),
            prospect_message=str(doc.get("prospect_message") or ""),
            result=result,
            agent_response=str(doc.get("agent_response") or ""),
            inbound_reply_id=str(doc["inbound_reply_id"])
            if doc.get("inbound_reply_id")
            else None,
            created_at=created_at,
        )

    async def create(
        self,
        *,
        workflow_id: str,
        lead_email: str,
        tool_name: AgentToolName | str,
        prospect_message: str,
        result: dict[str, Any],
        agent_response: str,
        inbound_reply_id: str | None = None,
    ) -> ToolExecutionRecord:
        now = datetime.now(UTC)
        doc_id = str(uuid4())
        name_value = tool_name.value if isinstance(tool_name, AgentToolName) else str(tool_name)
        doc: dict[str, Any] = {
            "_id": doc_id,
            "workflow_id": workflow_id,
            "lead_email": lead_email.lower(),
            "tool_name": name_value,
            "prospect_message": prospect_message,
            "result": result,
            "agent_response": agent_response,
            "inbound_reply_id": inbound_reply_id,
            "created_at": now,
        }
        await get_database()[self.COLLECTION].insert_one(doc)
        return self._doc_to_record(doc)

    async def list_for_workflow(
        self,
        workflow_id: str,
        *,
        limit: int = 50,
    ) -> list[ToolExecutionRecord]:
        cursor = (
            get_database()[self.COLLECTION]
            .find({"workflow_id": workflow_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        return [self._doc_to_record(doc) async for doc in cursor]


tool_execution_repository = ToolExecutionRepository()
