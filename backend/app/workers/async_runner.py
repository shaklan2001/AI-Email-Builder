import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.database import close_db, connect_db

T = TypeVar("T")


def run_async(coro: Awaitable[T]) -> T:
    return asyncio.run(coro)


async def with_database(operation: Callable[[], Awaitable[T]]) -> T:
    await connect_db()
    try:
        return await operation()
    finally:
        await close_db()
