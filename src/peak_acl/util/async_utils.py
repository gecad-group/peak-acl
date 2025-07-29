# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

"""
Async helpers.

Currently exposes :func:`safe_create_task`, a thin wrapper around
``asyncio.create_task`` that logs any exception raised by the background task
instead of letting it be swallowed silently.

Note
----
Uses the ``|`` union operator in the type hint (``str | None``), which requires
Python ≥ 3.10. Your project target is 3.9+, so this is fine at runtime (type
hints are ignored) but tools like mypy/pyright on 3.9 may complain unless
``from __future__ import annotations`` or ``typing.Optional[str]`` is used.
"""

from __future__ import annotations

import asyncio
import logging

log = logging.getLogger("peak_acl.async_utils")


# --------------------------------------------------------------------------- #
# safe_create_task
# --------------------------------------------------------------------------- #
def safe_create_task(coro, *, name: str | None = None) -> asyncio.Task:
    """Create an asyncio.Task and log any exception it raises.

    Parameters
    ----------
    coro :
        Awaitable/coroutine to schedule.
    name :
        Optional task name (Python 3.8+). Used only for logging/debugging.

    Returns
    -------
    asyncio.Task
        The created task (so callers can cancel/await if desired).

    Behavior
    --------
    A ``done_callback`` inspects the task; if it finished with an exception
    (and was not merely cancelled), the exception is logged with a traceback
    via ``log.exception``. Cancellation is ignored.
    """
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
