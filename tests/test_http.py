import asyncio
import socket

import pytest

from peak_acl.message import AgentIdentifier, AclMessage
from peak_acl.transport import start_server, HttpMtpClient


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.asyncio
async def test_http_client_server_roundtrip():
    received = []

    async def on_msg(env, acl):
        received.append((env, acl))

    port = _free_port()
    server, runner, site = await start_server(on_message=on_msg, bind_host="127.0.0.1", port=port)

    try:
        async with HttpMtpClient(retries=0) as client:
            to_ai = AgentIdentifier(f"receiver@localhost:{port}/JADE", [f"http://127.0.0.1:{port}/acc"])
            from_ai = AgentIdentifier("sender@localhost:1/JADE", ["http://127.0.0.1:1/acc"])
            msg = AclMessage("inform", content="ping")
            await client.send(to_ai, from_ai, msg, f"http://127.0.0.1:{port}/acc")
            await asyncio.sleep(0.1)
    finally:
        await server.close()

    assert len(received) == 1
    env, acl = received[0]
    assert acl.content == "ping"
    assert env.to_.name == to_ai.name
