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

# src/peak_acl/transport/http_mtp.py
"""
Inbound HTTP-MTP server compatible with JADE.

JADE posts a very minimal ``multipart/mixed`` body (no Content-Disposition).
Typical shape:

    --BOUNDARY
    Content-Type: application/xml

    <envelope>...</envelope>
    --BOUNDARY
    Content-Type: text/plain

    (ACL ...)
    --BOUNDARY--

Some agents reorder parts or add extra CR/LF breaks. The previous implementation
relied on ``aiohttp``'s multipart parser and ``part.name`` and would fail with
JADE traffic, causing JADE's Deliverer threads to block (“Deliverer stuck”).

This implementation:

* Reads the raw body (``await request.read()``).
* Extracts the boundary via regex.
* Parses multipart manually, tolerating variations.
* Identifies envelope/ACL by Content-Type + heuristics.
* Replies **immediately** with HTTP 200 to JADE; parsing happens in background.
* On error, logs a snippet and discards (does not block JADE).
* Delivers ``(Envelope, AclMessage)`` to a callback ``on_message`` or to
  an internal ``inbox`` queue.

A helper :func:`start_server` is provided for runtime integration.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Awaitable, Callable, Optional, Tuple, TYPE_CHECKING

from aiohttp import web

from ..message.envelope import Envelope
from ..parser import parse as parse_acl
from ..util.async_utils import safe_create_task  # background task wrapper

if TYPE_CHECKING:  # mypy / pylance only
    from ..message.acl import AclMessage

__all__ = ["HttpMtpServer", "start_server"]
_NOSET = object()  # sentinel (currently unused; kept for future configs)

_LOG = logging.getLogger("peak_acl.http_mtp")

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5 MiB
ACC_ENDPOINT = "/acc"
_BOUNDARY_RE = re.compile(r'boundary="?([^";]+)"?', re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Multipart helpers
# --------------------------------------------------------------------------- #
def _split_parts(raw: bytes, boundary_bytes: bytes) -> list[Tuple[bytes, bytes]]:
    """Split raw multipart payload into ``[(headers, body)]`` pairs.

    This is a tolerant splitter: it only separates parts and does not interpret
    ``Content-Transfer-Encoding`` or other headers.
    """
    marker = b"--" + boundary_bytes
    end_marker = marker + b"--"  # not explicitly used; kept for clarity

    # Normalize: trim surrounding whitespace / extra CRLF
    data = raw.strip()

    # Split by each marker occurrence (final marker included)
    chunks = data.split(marker)

    parts: list[Tuple[bytes, bytes]] = []
    for chunk in chunks:
        c = chunk.strip()
        if not c or c == b"--":
            continue
        if c.startswith(b"--"):  # final part marker (--BOUNDARY--)
            c = c[2:].lstrip()

        # Separate headers/body: prefer CRLF, fallback LF
        if b"\r\n\r\n" in c:
            hdr, body = c.split(b"\r\n\r\n", 1)
        elif b"\n\n" in c:
            hdr, body = c.split(b"\n\n", 1)
        else:
            hdr, body = b"", c

        # Trim trailing CR/LF before next boundary
        body = body.rstrip(b"\r\n")
        parts.append((hdr, body))

    return parts


def _guess_is_envelope(body: bytes) -> bool:
    """Heuristic: envelope starts with XML declaration."""
    return body.lstrip().startswith(b"<?xml")


def _guess_is_acl(body: bytes) -> bool:
    """Heuristic: JADE ACL strings start with '(' (ignore leading whitespace)."""
    return body.lstrip().startswith(b"(")


def _extract_envelope_acl(raw: bytes, boundary_bytes: bytes) -> Tuple[str, str]:
    """Extract ``(envelope_xml, acl_str)`` from a raw multipart body.

    Uses headers first, then heuristics, then positional fallback. Raises a
    ``ValueError`` if fewer than 2 parts are found.
    """
    parts = _split_parts(raw, boundary_bytes)
    if len(parts) < 2:
        raise ValueError(f"multipart inesperado (<2 partes); partes={len(parts)}")

    env_bytes: Optional[bytes] = None
    acl_bytes: Optional[bytes] = None

    # 1) Prefer Content-Type if present
    for hdr, body in parts:
        hlow = hdr.lower()
        if (b"application/xml" in hlow) and (env_bytes is None):
            env_bytes = body
            continue
        if (b"text/plain" in hlow) and (acl_bytes is None):
            acl_bytes = body
            continue

    # 2) Heuristics
    for _, body in parts:
        if env_bytes is None and _guess_is_envelope(body):
            env_bytes = body
            continue
        if acl_bytes is None and _guess_is_acl(body):
            acl_bytes = body
            continue

    # 3) Fallback: assume 1st part = envelope, 2nd = ACL
    if env_bytes is None:
        env_bytes = parts[0][1]
    if acl_bytes is None:
        # take the last non-envelope part
        for _, body in reversed(parts):
            if body is not env_bytes:  # identity check intentional
                acl_bytes = body
                break
        else:
            acl_bytes = parts[-1][1]

    # Decode to text
    env_txt = env_bytes.decode("utf-8", errors="replace").strip()
    acl_txt = acl_bytes.decode("utf-8", errors="replace").strip()

    # Sanity swap: if ACL/envelope seem inverted
    if (
        not _guess_is_acl(acl_bytes)
        and _guess_is_envelope(acl_bytes)
        and _guess_is_acl(env_bytes)
    ):
        env_txt, acl_txt = acl_txt, env_txt

    return env_txt, acl_txt


# --------------------------------------------------------------------------- #
# Main server class
# --------------------------------------------------------------------------- #
class HttpMtpServer:
    """Inbound HTTP-MTP server.

    Parameters
    ----------
    on_message :
        Optional async callback ``(env: Envelope, acl: AclMessage) -> Awaitable[None]``.
        If ``None``, messages are queued into :py:attr:`inbox`.
    client_max_size :
        Max accepted request size in bytes (default: 5 MiB).
    loop :
        Optional event loop to bind to ``aiohttp`` app (deprecated in aiohttp>=3.8).

    Attributes
    ----------
    inbox :
        ``asyncio.Queue[(Envelope, AclMessage)]`` used when no callback is set.
    app :
        Underlying ``aiohttp.web.Application`` instance.

    Notes
    -----
    * The server answers 200 OK immediately, then parses in a background task to
      avoid blocking JADE deliverers.
    * Errors during parsing are logged and ignored (message is dropped).
    """

    def __init__(
        self,
        on_message: Optional[Callable[[Envelope, "AclMessage"], Awaitable[None]]] = None,
        *,
        client_max_size: int = MAX_REQUEST_SIZE,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self._on_message = on_message
        self.inbox: "asyncio.Queue[tuple[Envelope, AclMessage]]" = asyncio.Queue()

        # aiohttp >=3.8 discourages passing loop; keep for backward compat
        if loop is not None:
            self.app = web.Application(client_max_size=client_max_size, loop=loop)
        else:
            self.app = web.Application(client_max_size=client_max_size)

        # Middlewares
        self.app.middlewares.extend([self._logging_middleware, self._error_middleware])

        # /acc route
        self.app.router.add_post(ACC_ENDPOINT, self._handle_post)

    # ------------------------------------------------------------------ #
    # Middlewares
    # ------------------------------------------------------------------ #
    @web.middleware
    async def _logging_middleware(self, request: web.Request, handler):
        """Log method/path/remote/status for each request."""
        resp = await handler(request)
        _LOG.info(
            "%s %s ← %s → %s",
            request.method,
            request.path_qs,
            request.remote,
            resp.status,
        )
        return resp

    @web.middleware
    async def _error_middleware(self, request: web.Request, handler):
        """Convert unexpected exceptions to HTTP 500 and log the traceback."""
        try:
            return await handler(request)
        except web.HTTPException:
            raise
        except Exception as exc:  # pragma: no cover
            _LOG.exception("Erro não tratado no HTTP-MTP")
            raise web.HTTPInternalServerError(text="internal error") from exc

    # ------------------------------------------------------------------ #
    # /acc handler
    # ------------------------------------------------------------------ #
    async def _handle_post(self, request: web.Request) -> web.StreamResponse:
        """Handle incoming POSTs to the ACC endpoint (non-blocking)."""
        raw = await request.read()

        # Immediate response (do not block JADE)
        resp = web.Response(
            text="ok",
            status=200,
            content_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "close"},
        )

        ctype = request.headers.get("Content-Type", "")
        m = _BOUNDARY_RE.search(ctype)
        if not m:
            _LOG.error("Sem boundary em Content-Type: %s", ctype)
            return resp

        boundary_bytes = m.group(1).encode("utf-8", "ignore")

        # Process in background (use safe_create_task to log exceptions)
        safe_create_task(self._process_raw(raw, boundary_bytes), name="mtp_process_raw")
        return resp

    # ------------------------------------------------------------------ #
    async def _process_raw(self, raw: bytes, boundary_bytes: bytes) -> None:
        """Parse raw multipart into Envelope + AclMessage and deliver it.

        Runs in a separate Task.
        """
        try:
            env_txt, acl_txt = _extract_envelope_acl(raw, boundary_bytes)

            # Debug snippets
            _LOG.debug(
                "MTP RAW (%dB) env=%dB acl=%dB",
                len(raw),
                len(env_txt),
                len(acl_txt),
            )
            _LOG.debug("MTP ENV snippet: %s", env_txt[:80].replace("\n", " "))
            _LOG.debug("MTP ACL snippet: %s", acl_txt[:80].replace("\n", " "))

            env = Envelope.from_xml(env_txt)
            acl = parse_acl(acl_txt)

        except ValueError as exc:
            # Known parse/format error
            sample = raw[:200].decode("utf-8", errors="replace").replace("\n", "\\n")
            _LOG.warning("Multipart parse error (%s). Raw[:200]=%r", exc, sample)
            return
        except Exception:
            # Unexpected error path
            sample = raw[:200].decode("utf-8", errors="replace").replace("\n", "\\n")
            _LOG.exception("Unexpected processing error. Raw[:200]=%r", sample)
            return

        # Deliver
        try:
            if self._on_message is not None:
                await self._on_message(env, acl)
            else:
                await self.inbox.put((env, acl))
            _LOG.debug(
                "MTP IN: %s -> %s (%dB)",
                env.from_.name,
                getattr(acl, "performative_upper", "?"),
                len(raw),
            )
        except Exception:  # pragma: no cover - external callback
            _LOG.exception("Erro no callback on_message (ignorado).")

    async def close(self):
        """Gracefully stop aiohttp runner/site if started via run()/start_server."""
        if hasattr(self, "_site") and self._site is not None:
            await self._site.stop()
        if hasattr(self, "_runner") and self._runner is not None:
            await self._runner.cleanup()

    # ------------------------------------------------------------------ #
    async def run(self, host: str = "0.0.0.0", port: int = 7777):
        """Blocking run helper (manual debug usage)."""
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, host, port)
        _LOG.info("HttpMtpServer a escutar em http://%s:%d%s", host, port, ACC_ENDPOINT)
        await self._site.start()
        try:
            await asyncio.Event().wait()  # block forever
        finally:
            await self.close()


# --------------------------------------------------------------------------- #
# start_server helper (used by runtime)
# --------------------------------------------------------------------------- #
async def start_server(
    *,
    on_message: Optional[Callable[[Envelope, "AclMessage"], Awaitable[None]]] = None,
    bind_host: str = "0.0.0.0",
    port: int = 7777,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    client_max_size: int = MAX_REQUEST_SIZE,
) -> tuple[HttpMtpServer, web.AppRunner, web.TCPSite]:
    """Convenience bootstrap for the HTTP-MTP server.

    Returns the server instance plus the runner/site objects so the caller can
    later stop/cleanup them if needed.
    """
    server = HttpMtpServer(
        on_message=on_message,
        client_max_size=client_max_size,
        loop=loop,
    )

    server._runner = web.AppRunner(server.app)
    await server._runner.setup()
    server._site = web.TCPSite(server._runner, bind_host, port)
    await server._site.start()

    _LOG.info(
        "HttpMtpServer a escutar em http://%s:%d%s", bind_host, port, ACC_ENDPOINT
    )

    return server, server._runner, server._site


# --------------------------------------------------------------------------- #
# Stand-alone debug
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7777)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    async def _print_msg(env: Envelope, acl: "AclMessage"):
        _LOG.info("Mensagem recebida: %s -> %s", env.from_.name, acl.performative_upper)

    async def _main():
        await start_server(on_message=_print_msg, bind_host=args.host, port=args.port)
        await asyncio.Event().wait()

    asyncio.run(_main())
