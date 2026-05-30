from pydantic import BaseModel, Field


class RunAgentToolsRequest(BaseModel):
    message: str = Field(..., min_length=1)
    lead_email: str = Field(..., min_length=3, alias="leadEmail")

    model_config = {"populate_by_name": True}


class AgentToolsRunData(BaseModel):
    selected_tool: str = Field(..., alias="selectedTool")
    tool_called: bool = Field(..., alias="toolCalled")
    tool_result: dict = Field(default_factory=dict, alias="toolResult")
    agent_response: str = Field(default="", alias="agentResponse")
    execution_id: str | None = Field(default=None, alias="executionId")

    model_config = {"populate_by_name": True}


class ToolExecutionData(BaseModel):
    id: str
    tool_name: str = Field(..., alias="toolName")
    lead_email: str = Field(..., alias="leadEmail")
    prospect_message: str = Field(..., alias="prospectMessage")
    agent_response: str = Field(..., alias="agentResponse")
    created_at: str = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}
