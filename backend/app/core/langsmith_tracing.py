"""Enable LangSmith tracing for LangGraph, LLM calls, and agent steps."""

import os

from app.core.config import settings


def setup_langsmith_tracing() -> bool:
    """
    Configure LangChain/LangSmith environment variables before graph or LLM use.

    Returns True when tracing was enabled.
    """
    if not settings.enable_langsmith_tracing:
        return False

    api_key = settings.langsmith_api_key.strip()
    if not api_key:
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGSMITH_API_KEY"] = api_key
    project = settings.langchain_project.strip()
    if project:
        os.environ["LANGCHAIN_PROJECT"] = project
    return True


def is_langsmith_tracing_enabled() -> bool:
    return os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true" and bool(
        os.environ.get("LANGSMITH_API_KEY", "").strip()
        or os.environ.get("LANGCHAIN_API_KEY", "").strip()
    )
