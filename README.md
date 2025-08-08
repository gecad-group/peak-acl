# peak-acl: FIPA-ACL parser & transport helpers for PEAK

[![PyPI](https://img.shields.io/pypi/v/peak-acl)](https://pypi.org/project/peak-acl/)
[![Python Versions](https://img.shields.io/pypi/pyversions/peak-acl)](https://pypi.org/project/peak-acl/)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://github.com/gecad-group/peak-acl/blob/main/LICENSE)

`peak-acl` is a Python library for parsing, constructing, and transporting
[FIPA-ACL](https://www.fipa.org/specs/fipa00061/SC00061G.html) messages. It
offers an ANTLR-powered parser, utilities for building and dispatching
messages, and optional HTTP-MTP transport compatible with JADE-based agents.
While designed for the [PEAK](https://github.com/gecad-group/peak-mas)
framework, it can also be used independently in any Python project.

---

## Features
The library supports the full FIPA-ACL message model with dictionary-style
access, provides SL0 helpers for Directory Facilitator interactions, includes an
ANTLR-based parser and optional HTTP-MTP client and server with automatic
retries, and offers a conversation manager plus routing utilities for
asynchronous workflows.

---

## Prerequisites
Python **3.9 or later** is required. A JADE ACC or compatible HTTP-MTP endpoint
is optional. Development requirements such as `pytest`, `mypy`, `black`, and
`isort` are available via the `dev` extra.

---

## Installation

```bash
pip install peak-acl
```
---

## Quick Start

Parse an ACL string:
```python
from peak_acl import parse

raw = "(inform :content \"hello\")"
msg = parse(raw)
print(msg.performative_upper)
print(msg['content'])
```

Serialize an `AclMessage`:
```python
from peak_acl.message import AclMessage
from peak_acl.message.serialize import dumps

m = AclMessage(performative="request", content="(do-something)")
print(dumps(m))
```

Send over HTTP-MTP:
```python
from peak_acl.transport import HttpMtpClient
from peak_acl.message import AgentIdentifier, AclMessage

sender = AgentIdentifier("me@host", ["http://localhost:7777/acc"])
receiver = AgentIdentifier("df@host", ["http://other:7777/acc"])
acl = AclMessage(performative="inform", content="hi")

async def main():
    async with HttpMtpClient() as client:
        await client.send(receiver, sender, acl, receiver.addresses[0])
```

Run an inbound HTTP-MTP server:
```python
import asyncio
from peak_acl.transport import start_server

async def on_message(env, acl):
    print("IN:", env.from_.name, acl.performative_upper)

async def main():
    await start_server(on_message=on_message, port=7777)
    await asyncio.Event().wait()

asyncio.run(main())
```

---

## Working with SL0 / DF Helpers
`peak_acl.sl0` provides a minimal AST and serializer for FIPA-SL0 to talk to
JADE's DF/AMS.

---

## Conversation Manager
`ConversationManager` helps implementing the FIPA-Request flow. Supply a
low-level `send_fn` and await the resulting `Future` for the reply.

---

## Events & Routing
`InboundDispatcher` plus `MessageTemplate` allow pattern-based callbacks for
incoming ACLs. See `peak_acl.runtime.classify_message` for predefined kinds.

---

## Roadmap
- Richer SL (beyond SL0) support.
- Optional IPv6-aware network utilities.
- Extended error handling for user-defined parameters.
- Sphinx documentation site populated from docstrings.

---

## License
`peak-acl` is licensed under the GNU GPL v3. See the `LICENSE` file for
details.

