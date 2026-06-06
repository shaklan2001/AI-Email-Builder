"""Shared fixtures for integration tests."""

import pytest

from app.workers.celery_app import celery_app


@pytest.fixture(autouse=True)
def celery_eager_mode() -> None:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
    yield
    celery_app.conf.update(
        task_always_eager=False,
        task_eager_propagates=False,
    )
