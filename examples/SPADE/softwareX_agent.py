from __future__ import annotations

import asyncio
import logging
import uuid

import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour

from peak_acl.message.aid import AgentIdentifier
from peak_acl.message.acl import AclMessage
from peak_acl.message.serialize import dumps as acl_dumps
from peak_acl.transport.http_mtp import HttpMtpServer
from peak_acl.transport.http_client import HttpMtpClient
from peak_acl.runtime import df_manager


JID = "sender@localhost"
PASSWORD = "SENDER_PASS"

JADE_HOST = "172.18.155.79"
JADE_ACC = "http://172.18.155.79:7778/acc"
JADE_TARGET = "da0@172.18.155.79:1099/JADE"

ACC_HOST, ACC_PORT = "0.0.0.0", 7777
PUBLIC_HOST, PUBLIC_PORT = "localhost", 7777

MY_AID = AgentIdentifier(
    name=f"{JID.split('@')[0]}@{PUBLIC_HOST}:1500/SPADE",
    addresses=[f"http://{PUBLIC_HOST}:{PUBLIC_PORT}/acc"],
)
DF_AID = AgentIdentifier(f"df@{JADE_HOST}:1099/JADE", [JADE_ACC])
TARGET_AID = AgentIdentifier(JADE_TARGET, [JADE_ACC])

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("peak-acl-spade-example")


class BridgeAgent(Agent):
    class StartACC(OneShotBehaviour):
        async def run(self) -> None:
            me: BridgeAgent = self.agent  # type: ignore[assignment]

            async def on_incoming(env, acl: AclMessage) -> None:
                perf = acl.performative.upper()
                cid = acl.conversation_id or ""
                log.info("IN ← %s cid=%s content=%r", perf, cid, acl.content)
                norm = perf.replace("-", "_")
                if norm in ("ACCEPT_PROPOSAL", "ACCEPT"):
                    print("They accepted the offer I proposed.")
                elif norm in ("REJECT_PROPOSAL", "REFUSE"):
                    print("They refused the offer I proposed.")

            me.http = HttpMtpServer(  # type: ignore[attr-defined]
                on_message=on_incoming,
                host=ACC_HOST,
                port=ACC_PORT,
            )
            await me.http.start()
            log.info("ACC listening at http://%s:%s/acc", ACC_HOST, ACC_PORT)

    class RegisterDF(OneShotBehaviour):
        async def run(self) -> None:
            async with HttpMtpClient() as http:
                await df_manager.register(
                    my_aid=MY_AID,
                    df_aid=DF_AID,
                    services=[("spade-bridge", "interop")],
                    http_client=http,
                )
                log.info("DF.register sent.")

    class TalkToDummy(OneShotBehaviour):
        async def run(self) -> None:
            cid = str(uuid.uuid4())
            conv_id = f'"{cid}"'
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
            log.debug("ACL SENT:\n%s", acl_dumps(req))
            async with HttpMtpClient() as client:
                await client.send(
                    to=TARGET_AID,
                    sender=MY_AID,
                    acl=req,
                    url=JADE_ACC,
                )

    class KeepAlive(CyclicBehaviour):
        async def run(self) -> None:
            await asyncio.sleep(1)

    async def setup(self) -> None:
        log.info("Starting SPADE agent: %s", self.jid)
        self.add_behaviour(self.StartACC())
        self.add_behaviour(self.RegisterDF())
        self.add_behaviour(self.TalkToDummy())
        self.add_behaviour(self.KeepAlive())


async def main() -> None:
    ag = BridgeAgent(JID, PASSWORD)
    await ag.start(auto_register=True)
    log.info("SPADE agent started.")
    await spade.wait_until_finished(ag)


if __name__ == "__main__":
    spade.run(main())
