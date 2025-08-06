# peak-acl: FIPA-ACL parser & transport helpers for PEAK

[![PyPI](https://img.shields.io/pypi/v/peak-acl)](https://pypi.org/project/peak-acl/)
[![Python Versions](https://img.shields.io/pypi/pyversions/peak-acl)](https://pypi.org/project/peak-acl/)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)

`peak-acl` is a lightweight package that parses, builds and transports
[FIPA-ACL](https://www.fipa.org/specs/fipa00061/SC00061G.html) messages with
first-class support for JADE-compatible HTTP-MTP. It integrates with the
[PEAK](https://github.com/gecad-group/peak-mas) framework but can be used in any
Python project.

---

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Working with SL0 / DF Helpers](#working-with-sl0--df-helpers)
- [Conversation Manager](#conversation-manager)
- [Events & Routing](#events--routing)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features
- ✅ **Full FIPA-ACL message model** (`performative`, `sender`, `receiver`, ...).
- ✅ **Dict-like access** on `AclMessage` (`msg["content"]`, `msg.get(...)`).
- ✅ **ANTLR-based FIPA-ACL parser** → `AclMessage` objects.
- ✅ **SL0 helpers** for Directory Facilitator interactions.
- ✅ **HTTP-MTP client & server** with automatic retries.
- ✅ **Conversation manager** implementing the FIPA-Request protocol.
- ✅ **Utilities** for message routing and async helpers.

---

## Prerequisites
- Python **>= 3.9**
- Optional: a JADE ACC or compatible HTTP-MTP endpoint.

Development requirements are provided under the `dev` extra (pytest, mypy, black, isort, ...).

---

## Installation

```bash
pip install peak-acl
```

To work on the project from source:

```bash
git clone https://github.com/gecad-group/peak-acl.git
pip install -e .[dev]
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

## Documentation
HTML API docs are generated with **Sphinx** using the
[`furo`](https://github.com/pradyunsg/furo) theme.

```bash
pip install -e .[docs]
make -C docs html
```

Open `docs/_build/html/index.html` in your browser.

---

## Roadmap
- Richer SL (beyond SL0) support.
- Optional IPv6-aware network utilities.
- Extended error handling for user-defined parameters.
- Sphinx documentation site populated from docstrings.

---

## Contributing
Pull requests are welcome! For significant changes please open a discussion
first.

- Format code with **black** and **isort**.
- Run tests with **pytest**.
- Follow Conventional Commits when possible.

---

## License
`peak-acl` is licensed under the GNU GPL v3. See the `LICENSE` file for
details.

