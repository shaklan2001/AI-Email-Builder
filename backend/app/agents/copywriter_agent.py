"""Backward-compatible alias for the email generation agent."""

from app.agents.email_generation_agent import (
    EmailGenerationAgent,
    email_generation_agent,
)

CopywriterAgent = EmailGenerationAgent
copywriter_agent = email_generation_agent
