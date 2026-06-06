import os

import pytest

from app.core import langsmith_tracing
from app.core.config import Settings


@pytest.fixture(autouse=True)
def _clear_langsmith_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "LANGCHAIN_TRACING_V2",
        "LANGCHAIN_API_KEY",
        "LANGSMITH_API_KEY",
        "LANGCHAIN_PROJECT",
    ):
        monkeypatch.delenv(key, raising=False)


def test_setup_langsmith_tracing_no_op_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        langsmith_tracing.settings,
        "langsmith_api_key",
        "",
        raising=False,
    )
    assert langsmith_tracing.setup_langsmith_tracing() is False
    assert os.environ.get("LANGCHAIN_TRACING_V2") is None


def test_setup_langsmith_tracing_enables_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        langsmith_tracing.settings,
        "langsmith_api_key",
        "lsv2_test_key",
        raising=False,
    )
    monkeypatch.setattr(
        langsmith_tracing.settings,
        "enable_langsmith_tracing",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        langsmith_tracing.settings,
        "langchain_project",
        "test-project",
        raising=False,
    )

    assert langsmith_tracing.setup_langsmith_tracing() is True
    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "lsv2_test_key"
    assert os.environ["LANGCHAIN_API_KEY"] == "lsv2_test_key"
    assert os.environ["LANGCHAIN_PROJECT"] == "test-project"
    assert langsmith_tracing.is_langsmith_tracing_enabled() is True


def test_setup_langsmith_tracing_respects_disable_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        langsmith_tracing.settings,
        "langsmith_api_key",
        "lsv2_test_key",
        raising=False,
    )
    monkeypatch.setattr(
        langsmith_tracing.settings,
        "enable_langsmith_tracing",
        False,
        raising=False,
    )

    assert langsmith_tracing.setup_langsmith_tracing() is False
    assert os.environ.get("LANGCHAIN_TRACING_V2") is None


def test_settings_load_langsmith_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_API_KEY", "lsv2_from_env")
    settings = Settings()
    assert settings.langsmith_api_key == "lsv2_from_env"
