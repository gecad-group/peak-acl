# PEAK-ACL: Python-based framework for heterogenous agent communities - Agent Communication Language

[![PyPI](https://img.shields.io/pypi/v/peak-acl)](https://pypi.org/project/peak-acl/)
[![Python Versions](https://img.shields.io/pypi/pyversions/peak-acl)](https://pypi.org/project/peak-acl/)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)
[![code style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)
[![imports isort](https://img.shields.io/static/v1?label=imports\&message=isort\&color=blue\&labelColor=orange)](https://pycqa.github.io/isort/)

`peak-acl` is a Python library to **parse, build, route and transport**
[FIPA-ACL](https://www.fipa.org/specs/fipa00061/SC00061G.html) messages.
It provides an **ANTLR-powered parser**, message builders/serializers,
**SL0 helpers** for DF/AMS interaction, and optional **HTTP-MTP** client/server
compatible with **JADE**.
Although designed for the [PEAK](https://github.com/gecad-group/peak-mas)
ecosystem, it can be used **standalone** in any Python project.

---

## Table of Contents

* [Features](#features)
* [Compatibility](#compatibility)
* [Installation](#installation)
* [Quick Start](#quick-start)
  * [Parse an ACL string](#parse-an-acl-string)
  * [Build and serialize an AclMessage](#build-and-serialize-an-aclmessage)
  * [Send over HTTP-MTP (client)](#send-over-http-mtp-client)
  * [Run an inbound HTTP-MTP server](#run-an-inbound-http-mtp-server)
* [SL0 / DF Helpers](#sl0--df-helpers)
* [Conversation Manager](#conversation-manager)
* [Events & Routing](#events--routing)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [Changelog](#changelog)
* [License](#license)

---

## Features

* **Full FIPA-ACL message model** with dict-style accessors.
* **ANTLR-based** parser and safe serializers.
* **HTTP-MTP** client/server (JADE ACC compatible) with retries.
* **SL0 utilities** for DF/AMS interactions.
* **Conversation Manager** for FIPA-Request flows.
* **Inbound routing & templates** for async workflows.

---

## Compatibility

* **Python:** requires **>= 3.9**; tested on **3.9, 3.10, 3.11**.
* **Runtime dependencies (minimums):**
  `antlr4-python3-runtime >= 4.13`, `aiohttp >= 3.7`.
* **HTTP-MTP:** compatible with **JADE ACC** or other endpoints like
  `http://<host>:7777/acc` or `http://<jade-host>:7778/acc`.

---

## Installation

```bash
pip install "peak-acl @ git+https://https://github.com/gecad-group/peak-acl"
```

---

## Quick Start

### Parse an ACL string

```python
from peak_acl.parse import parse

raw = '(inform :content "hello")'
msg = parse(raw)

print(msg.performative_upper)  # INFORM
print(msg["content"])          # hello
```

### Build and serialize an `AclMessage`

```python
from peak_acl.message.acl import AclMessage
from peak_acl.message.serialize import dumps

m = AclMessage(performative="request", content="(do-something)")
print(dumps(m))
```

### Send over HTTP-MTP (client)

```python
import asyncio
from peak_acl.transport.http_client import HttpMtpClient
from peak_acl.message.aid import AgentIdentifier
from peak_acl.message.acl import AclMessage

sender   = AgentIdentifier("me@host", ["http://localhost:7777/acc"])
receiver = AgentIdentifier("df@host", ["http://other:7777/acc"])

acl = AclMessage(performative="inform", content="hi")

async def main():
    async with HttpMtpClient() as client:
        await client.send(
            to=receiver,
            sender=sender,
            acl=acl,
            url=receiver.addresses[0],
        )

asyncio.run(main())
```

### Run an inbound HTTP-MTP server

```python
import asyncio
from peak_acl.transport.http_mtp import HttpMtpServer

async def on_message(env, acl):
    print("IN:", env.from_.name, acl.performative_upper)

async def main():
    server = HttpMtpServer(on_message=on_message, host="0.0.0.0", port=7777)
    await server.start()
    try:
        await asyncio.Event().wait()
    finally:
        await server.stop()

asyncio.run(main())
```

> **JADE interop:** use ACC endpoints like `http://<jade-host>:7778/acc` in the
> agent’s `addresses`. `AgentIdentifier` can hold multiple addresses; pass the
> selected URL to `HttpMtpClient.send(...)`.

---

## SL0 / DF Helpers

`peak_acl.sl0` provides a minimal AST and serializer for **FIPA-SL0**, making it
straightforward to query the **Directory Facilitator (DF)** and **AMS** from
Python. It pairs naturally with `AclMessage.content` for JADE compatibility.

---

## Conversation Manager

`ConversationManager` streamlines **FIPA-Request** exchanges:

* Provide a low-level `send_fn(to, sender, acl)` coroutine.
* The manager tracks `conversation-id`, awaits `{AGREE|REFUSE}` then
  `{INFORM|FAILURE}`.
* `await` the returned `Future` to get the terminal reply (or timeout/cancel).

Ideal for coordinating multi-step interactions without cluttering behaviours
with state machines.

---

## Events & Routing

Use `InboundDispatcher` and `MessageTemplate` to register callbacks **by
pattern** (performative, sender, ontology, conversation-id, etc.).
See `peak_acl.runtime.classify_message` for predefined kinds that help you route
common cases quickly.

---

## Roadmap

* Richer **SL** (beyond SL0) support.
* Optional **IIOP-MTP** networking utilities.
* Extended error handling for **user-defined parameters**.

---

## Contributing

Pull requests are welcome. For major changes, please start a discussion first.

**Dev setup**

```bash
git clone https://github.com/gecad-group/peak-acl
cd peak-acl
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

**Run checks**

```bash
pytest
mypy peak_acl
isort -c .
black --check .
```

**Commit style**

* Follow **Conventional Commits** for messages.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of notable changes to `peak-acl`.

---

## License

`peak-acl` is free and open-source software licensed under the **GNU General
Public License v3.0**. See [LICENSE](LICENSE) for details.
