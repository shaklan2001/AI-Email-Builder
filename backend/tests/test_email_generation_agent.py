"""Email generation agent — types, inputs, MongoDB persistence."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.email_generation_agent import EmailGenerationAgent, _validate_email_payload
from app.schemas.campaign import CampaignData
from app.schemas.email import GeneratedEmailContent
from app.schemas.workflow import WorkflowDefinition, WorkflowStep
from app.services.email_type import infer_email_type


def test_validate_email_payload() -> None:
    content = _validate_email_payload(
        {
            "subject": "Hello",
            "html_content": "<p>Hi</p>",
            "plain_text_content": "Hi",
        },
    )
    assert content is not None
    assert content.final_user_version.subject == "Hello"


def test_infer_email_types() -> None:
    steps = [
        WorkflowStep(id="s1", type="send_email", name="Launch"),
        WorkflowStep(id="s2", type="wait"),
        WorkflowStep(id="s3", type="reply_condition"),
        WorkflowStep(id="s6", type="send_email", name="Follow Up"),
    ]
    assert infer_email_type(steps[0], steps) == "promotional"
    assert infer_email_type(steps[3], steps) == "follow_up"


def test_email_generation_context_includes_inputs() -> None:
    campaign = CampaignData(
        product_info="Widget",
        audience="SMBs",
        cta="Book Demo",
        landing_page="https://example.com",
        product_image="https://example.com/img.png",
        tone="Professional",
    )
    ctx = campaign.email_generation_context()
    assert "Product: Widget" in ctx
    assert "Website: https://example.com" in ctx
    assert "Image URL: https://example.com/img.png" in ctx


@pytest.mark.asyncio
async def test_generate_emails_for_workflow() -> None:
    llm = MagicMock()
    llm.generate = AsyncMock(
        return_value='{"subject":"S","html_content":"<p>H</p>","plain_text_content":"H"}',
    )
    agent = EmailGenerationAgent(llm=llm)
    campaign = CampaignData(
        product_info="CRM",
        audience="Founders",
        tone="Professional",
        cta="Learn More",
    )
    definition = WorkflowDefinition(
        steps=[
            WorkflowStep(id="s1", type="send_email", name="Intro"),
            WorkflowStep(id="s6", type="send_email", name="Follow Up"),
        ],
    )
    with patch(
        "app.agents.email_generation_agent.email_template_repository.sync_from_workflow",
        new_callable=AsyncMock,
    ):
        result = await agent.generate_emails_for_workflow(
            campaign,
            definition,
            workflow_id="wf_test123456789",
            persist=True,
        )
    send_steps = [s for s in result.steps if s.type == "send_email"]
    assert len(send_steps) == 2
    assert all(s.email is not None for s in send_steps)
    assert llm.generate.await_count >= 2


@pytest.mark.asyncio
async def test_persist_syncs_templates() -> None:
    from unittest.mock import patch

    agent = EmailGenerationAgent()
    content = GeneratedEmailContent.from_ai_draft(
        subject="Subj",
        html_content="<p>Body</p>",
        plain_text_content="Body",
    )
    definition = WorkflowDefinition(
        steps=[
            WorkflowStep(id="s1", type="send_email", name="Intro", email=content),
        ],
    )
    with patch(
        "app.agents.email_generation_agent.email_template_repository.sync_from_workflow",
        new_callable=AsyncMock,
    ) as sync:
        await agent.persist_workflow_emails(
            workflow_id="wf_test123456789",
            definition=definition,
        )
    sync.assert_awaited_once()
    templates = sync.await_args.kwargs["templates"]
    assert templates[0]["step_id"] == "s1"
    assert templates[0]["subject"] == "Subj"
