# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Santiago Bossa
#
# This file is part of peak-acl.
#
# peak-acl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# peak-acl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with peak-acl.  If not, see the LICENSE file in the project root.

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
