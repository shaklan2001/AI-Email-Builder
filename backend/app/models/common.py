from datetime import UTC, datetime

from pydantic import Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
