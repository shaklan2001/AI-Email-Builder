from unittest.mock import AsyncMock, patch

import pytest

from app.services.chat_thread_service import chat_thread_service


@pytest.mark.asyncio
async def test_reset_thread_clears_messages() -> None:
    with (
        patch(
            "app.services.chat_thread_service.workflow_repository.get_by_id",
            new_callable=AsyncMock,
            return_value=object(),
        ),
        patch(
            "app.services.persistence.save_conversation_state",
            new_callable=AsyncMock,
        ) as save_state,
    ):
        result = await chat_thread_service.reset_thread(
            user_id="user_1",
            thread_id="wf_abc123456789",
        )

    assert result is not None
    assert result.data.messages == []
    assert result.data.stage == "discovery"
    save_state.assert_awaited_once()
    saved_state = save_state.await_args.args[2]
    assert saved_state["messages"] == []
    assert saved_state.get("workflow") is None
