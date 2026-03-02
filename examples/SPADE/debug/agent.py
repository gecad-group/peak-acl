# agents/agent.py
from __future__ import annotations

"""
Example SPADE agent using peak-acl to interoperate with a JADE platform over HTTP-MTP.

This agent:
- starts a local HTTP-MTP ACC (peak-acl HttpMtpServer)
- registers itself in the JADE DF using FIPA-Agent-Management
- sends a PROPOSE to a dummy JADE agent
- prints a human-readable message when the JADE agent accepts or rejects the offer
"""

import asyncio
import logging
import uuid

import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour

from peak_acl.message.aid import AgentIdentifier
from peak_acl.message.acl import AclMessage
from peak_acl.message.serialize import dumps as acl_dumps
from peak_acl.transport.http_mtp import HttpMtpServer
from peak_acl.transport.http_client import HttpMtpClient
from peak_acl.runtime import df_manager

# =============================================================================
# Optional: HTTP-MTP wire logging (OUT / IN) for debugging
# =============================================================================


def enable_http_mtp_logging() -> None:
    """
    Monkey-patch aiohttp.ClientSession.post so that every HTTP-MTP POST
    is printed as a raw HTTP request (headers + multipart body) before
    being actually sent. Useful to debug interoperability with JADE.
    """
    import aiohttp
    import re
    import sys
    import urllib.parse

    orig_post = aiohttp.ClientSession.post

    def logged_post(self, url, *args, **kwargs):  # type: ignore[override]
        headers = dict(kwargs.get("headers", {}))
        data = kwargs.get("data", b"")

        # Exact body bytes
        if isinstance(data, (bytes, bytearray, memoryview)):
            body_bytes = bytes(data)
        elif hasattr(data, "read"):
            try:
                body_bytes = data.read()
            except Exception:
                body_bytes = b"<unreadable-stream>"
        else:
            try:
                body_bytes = bytes(data)
            except Exception:
                body_bytes = str(data).encode("utf-8", "replace")

        # Extract boundary and host/path
        ctype = headers.get("Content-Type", "")
        m = re.search(r'boundary="?([^";]+)"?', ctype, flags=re.IGNORECASE)
        boundary = m.group(1) if m else "<no-boundary>"

        parsed = urllib.parse.urlparse(str(url))
        netloc = parsed.netloc or "<host>"
        path = parsed.path or "/"

        # Copy-paste friendly HTTP block
        print("\n-----8<----- HTTP MTP OUT (pre-send) -----8<-----")
        print(f"POST {path} HTTP/1.1")
        print(f"Host: {netloc}")
        for k, v in headers.items():
            if k.lower() == "host":
                continue
            print(f"{k}: {v}")
        print(f"Content-Length: {len(body_bytes)}\n")
        try:
            sys.stdout.flush()
            sys.stdout.buffer.write(body_bytes + b"\n")
        except Exception:
            print(body_bytes.decode("utf-8", errors="replace"))
        print(f"-----8<----- END (boundary={boundary}) -----8<-----\n")
        sys.stdout.flush()

        # Send exactly these bytes (aiohttp will re-add Content-Length)
        headers.pop("Content-Length", None)
        kwargs["headers"] = headers
        kwargs["data"] = body_bytes

        return orig_post(self, url, *args, **kwargs)

    aiohttp.ClientSession.post = logged_post  # type: ignore[assignment]


def enable_http_mtp_in_logging() -> None:
    """
    Monkey-patch aiohttp Request.read() so that every HTTP-MTP POST /acc
    received by the local ACC is printed as raw HTTP (headers + multipart).
    This mirrors enable_http_mtp_logging() for INBOUND messages.
    """
    import re
    import sys
    from aiohttp.web_request import Request

    orig_read = Request.read

    async def logged_read(self: Request):  # type: ignore[override]
        data = await orig_read(self)

        if (
            getattr(self, "_mtp_in_logged", False) is False
            and self.method == "POST"
            and self.path == "/acc"
        ):
            setattr(self, "_mtp_in_logged", True)

            headers_seq = list(self.headers.items())
            headers_map = dict(self.headers)

            ctype = headers_map.get("Content-Type", "")
            m = re.search(r'boundary="?([^";]+)"?', ctype, flags=re.IGNORECASE)
            boundary = m.group(1) if m else "<no-boundary>"

            # HTTP version if available
            try:
                ver = getattr(self, "version", None)
                http_ver = f"HTTP/{ver.major}.{ver.minor}" if ver else "HTTP/1.1"
            except Exception:
                http_ver = "HTTP/1.1"

            # Path + query, if any
            try:
                path = self.rel_url.raw_path
                if self.rel_url.query_string:
                    path += "?" + self.rel_url.query_string
            except Exception:
                path = self.path or "/acc"

            host = headers_map.get("Host", getattr(self, "host", "<host>"))

            # Copy-paste friendly HTTP block
            print("\n-----8<----- HTTP MTP IN -----8<-----")
            print(f"POST {path} {http_ver}")
            print(f"Host: {host}")
            for k, v in headers_seq:
                if k.lower() == "host":
                    continue
                print(f"{k}: {v}")
            print(f"Content-Length: {len(data)}\n")
            try:
                sys.stdout.flush()
                sys.stdout.buffer.write(data + b"\n")
            except Exception:
                print(data.decode("utf-8", errors="replace"))
            print(f"-----8<----- END (boundary={boundary}) -----8<-----\n")
            sys.stdout.flush()

            # Put bytes back so other readers still see the body
            try:
                self._read_bytes = data  # type: ignore[attr-defined]
            except Exception:
                pass

        return data

    Request.read = logged_read  # type: ignore[assignment]


# =============================================================================
# Configuration
# =============================================================================

JID = "sender@localhost"
PASSWORD = "SENDER_PASS"

# JADE main container / HTTP-MTP ACC address
JADE_HOST = "172.18.155.79"
JADE_ACC = "http://172.18.155.79:7778/acc"
JADE_TARGET = "da0@172.18.155.79:1099/JADE"

# Local ACC (peak-acl HttpMtpServer) bind address
ACC_HOST, ACC_PORT = "0.0.0.0", 7777
PUBLIC_HOST, PUBLIC_PORT = "localhost", 7777

MY_AID = AgentIdentifier(
    name=f"{JID.split('@')[0]}@{PUBLIC_HOST}:1500/SPADE",
    addresses=[f"http://{PUBLIC_HOST}:{PUBLIC_PORT}/acc"],
)
DF_AID = AgentIdentifier(f"df@{JADE_HOST}:1099/JADE", [JADE_ACC])
TARGET_AID = AgentIdentifier(JADE_TARGET, [JADE_ACC])

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("peak-acl-spade-example")


# =============================================================================
# SPADE Agent
# =============================================================================


class agent(Agent):
    """
    SPADE agent that:
    - exposes a local HTTP-MTP ACC
    - registers itself in the JADE DF
    - sends a PROPOSE to a JADE dummy agent
    - interprets ACCEPT/REJECT performatives
    """

    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        self._inbox: dict[str, asyncio.Queue[AclMessage]] = {}

    # --------------------------------------------------------------------- #
    # ACC bootstrap                                                          #
    # --------------------------------------------------------------------- #

    class StartACC(OneShotBehaviour):
        async def run(self) -> None:
            """
            Start the local HTTP-MTP ACC (HttpMtpServer) and attach the
            on_incoming callback that routes messages into _inbox queues
            keyed by conversation-id.
            """
            me: "agent" = self.agent  # type: ignore[assignment]

            async def on_incoming(env, acl: AclMessage) -> None:
                perf = getattr(acl, "performative", "?")
                cid = acl.conversation_id or "no-cid"
                log.info("HTTP-IN ← perf=%s cid=%s content=%r", perf, cid, acl.content)
                if acl.conversation_id:
                    q = me._inbox.setdefault(acl.conversation_id, asyncio.Queue())
                    await q.put(acl)

            bound = False
            try:
                me.http = HttpMtpServer(  # type: ignore[attr-defined]
                    on_message=on_incoming,
                    host=ACC_HOST,
                    port=ACC_PORT,
                )
                bound = True
                log.debug("HttpMtpServer: bound in __init__(host, port).")
            except TypeError:
                me.http = HttpMtpServer(on_message=on_incoming)  # type: ignore[attr-defined]

            if not bound:
                # Try a few common method names to bind the server
                for name, args in [
                    ("start", (ACC_HOST, ACC_PORT)),
                    ("start", ()),
                    ("serve", (ACC_HOST, ACC_PORT)),
                    ("serve", ()),
                    ("listen", (ACC_HOST, ACC_PORT)),
                    ("listen", ()),
                    ("run", (ACC_HOST, ACC_PORT)),
                    ("run", ()),
                ]:
                    meth = getattr(me.http, name, None)  # type: ignore[attr-defined]
                    if not meth:
                        continue
                    try:
                        res = meth(*args)
                        if asyncio.iscoroutine(res):
                            await res
                        bound = True
                        log.debug("HttpMtpServer: bound via %s%r", name, args)
                        break
                    except TypeError:
                        continue

            if bound:
                log.info("ACC listening at http://%s:%s/acc", ACC_HOST, ACC_PORT)
            else:
                log.warning(
                    "HttpMtpServer did not expose a bind API; using internal port."
                )

    # --------------------------------------------------------------------- #
    # DF registration                                                        #
    # --------------------------------------------------------------------- #

    class RegisterDF(OneShotBehaviour):
        async def run(self) -> None:
            """
            Register this agent in the JADE DF over HTTP-MTP using peak-acl's
            df_manager helper.
            """
            async with HttpMtpClient() as http:
                await df_manager.register(
                    my_aid=MY_AID,
                    df_aid=DF_AID,
                    services=[("spade-bridge", "interop")],
                    http_client=http,
                )
                log.info("DF.register sent via peak-acl df_manager helper.")

    # --------------------------------------------------------------------- #
    # Interaction with JADE dummy agent                                      #
    # --------------------------------------------------------------------- #

    class TalkToDummy(OneShotBehaviour):
        async def run(self) -> None:
            """
            Send a PROPOSE with a simple offer to the JADE dummy agent and
            wait for a single reply. If the reply performative is an
            ACCEPT/ACCEPT-PROPOSAL or REJECT/REJECT-PROPOSAL, print a
            human-readable message.
            """
            cid = str(uuid.uuid4())
            conv_id = f'"{cid}"'  # quoted conversation-id as in other examples

            offer = '(offer :item "transport-plan-1" :price 42)'

            req = AclMessage(
                performative="propose",
                protocol="fipa-propose",
                ontology="example",
                content=offer,
                conversation_id=conv_id,
                sender=MY_AID,
                receivers=[TARGET_AID],
            )

            log.info("PROPOSE → %s | cid=%s", TARGET_AID.name, cid)
            log.debug("ACL SENT (peak-acl):\n%s", acl_dumps(req))

            async with HttpMtpClient() as client:
                q = self.agent._inbox.setdefault(cid, asyncio.Queue())  # type: ignore[attr-defined]
                await client.send(TARGET_AID, MY_AID, req, JADE_ACC)

                first = await asyncio.wait_for(q.get(), timeout=45)

            perf = first.performative.upper()
            log.info("First reply: %s content=%r", perf, first.content)

            # Accept dashes (JADE style) and underscores if any
            norm = perf.replace("-", "_")

            if norm in ("ACCEPT_PROPOSAL", "ACCEPT"):
                print("They accepted the offer I proposed.")
                log.info("They accepted the offer I proposed.")
            elif norm in ("REJECT_PROPOSAL", "REFUSE"):
                print("They refused the offer I proposed.")
                log.info("They refused the offer I proposed.")
            else:
                log.info("Unexpected reply: perf=%s content=%r", perf, first.content)

    # --------------------------------------------------------------------- #
    # Keep the SPADE agent alive                                             #
    # --------------------------------------------------------------------- #

    class KeepAlive(CyclicBehaviour):
        async def run(self) -> None:
            await asyncio.sleep(1)

    # --------------------------------------------------------------------- #
    # SPADE lifecycle                                                        #
    # --------------------------------------------------------------------- #

    async def setup(self) -> None:
        # Enable optional wire-level HTTP-MTP logging (OUT and IN) before
        # any peak-acl HTTP-MTP traffic happens.
        enable_http_mtp_logging()
        enable_http_mtp_in_logging()

        log.info("Starting SPADE agent: %s", self.jid)
        self.add_behaviour(self.StartACC())
        self.add_behaviour(self.RegisterDF())
        self.add_behaviour(self.TalkToDummy())
        self.add_behaviour(self.KeepAlive())


# =============================================================================
# main
# =============================================================================


async def main() -> None:
    ag = agent(JID, PASSWORD)
    await ag.start(auto_register=True)
    log.info("SPADE agent started.")
    await spade.wait_until_finished(ag)


if __name__ == "__main__":
    spade.run(main())
