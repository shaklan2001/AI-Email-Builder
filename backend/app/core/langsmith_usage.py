"""Attach Groq token usage to the active LangSmith run when available."""


def record_llm_token_usage(usage: object | None) -> None:
    if usage is None:
        return
    try:
        from langsmith import get_current_run_tree
    except ImportError:
        return

    run = get_current_run_tree()
    if run is None:
        return

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    if prompt_tokens is None and completion_tokens is None:
        return

    run.metadata["usage_metadata"] = {
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }
