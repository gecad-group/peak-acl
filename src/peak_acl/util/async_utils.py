# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

import asyncio
import logging

log = logging.getLogger("peak_acl.async_utils")

def safe_create_task(coro, *, name: str | None = None) -> asyncio.Task:
    """Create a task and log any exception it raises."""
    task = asyncio.create_task(coro, name=name)
    def _done(t: asyncio.Task):
        try:
            exc = t.exception()
        except asyncio.CancelledError:
            return
        if exc:
            log.exception("Background task %s failed", name or coro, exc_info=exc)
    task.add_done_callback(_done)
    return task