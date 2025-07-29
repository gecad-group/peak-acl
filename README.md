# peak-acl: FIPA-ACL parser & transport helpers for PEAK

> **PEAK-ACL** is a small library that parses, builds and transports FIPA-ACL messages, with first-class support for JADE-compatible HTTP-MTP. It is designed to plug into the [PEAK](https://github.com/gecad-group/peak-mas) ecosystem but can be used standalone in any Python project.

---

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [PyPI](#pypi)
  - [From source / dev mode](#from-source--dev-mode)
- [Quick Start](#quick-start)
  - [Parse an ACL string](#parse-an-acl-string)
  - [Serialize an `AclMessage`](#serialize-an-aclmessage)
  - [Send over HTTP-MTP](#send-over-http-mtp)
  - [Run an inbound HTTP-MTP server](#run-an-inbound-http-mtp-server)
- [Working with SL0 / DF Helpers](#working-with-sl0--df-helpers)
- [Conversation Manager](#conversation-manager)
- [Events & Routing](#events--routing)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features
- ✅ **Full FIPA-ACL message model** (`performative`, `sender`, `receiver`, etc.), JADE-compatible.
- ✅ **Dict-like accessors** on `AclMessage` (`msg["content"]`, `"ontology" in msg`, `msg.get(...)`).
- ✅ **ANTLR-based FIPA-ACL parser** → `AclMessage` objects.
- ✅ **SL0 implementation** for Directory Facilitator (DF/AMS) interactions.
- ✅ **HTTP-MTP client & server** (multipart/mixed) with retries/backoff and tolerant multipart parsing.
- ✅ **Conversation manager** for the FIPA-Request protocol (REQUEST -> {AGREE|REFUSE} -> {INFORM|FAILURE}).
- ✅ **Utilities**: message routing, content decoding, async helpers.

---

## Prerequisites
- Python **>= 3.9**
- Optional (at runtime): a JADE ACC or compatible HTTP-MTP endpoint to talk to.

Development requirements are listed under the `dev` extra (pytest, mypy, black, isort, etc.).

---

## Installation

### PyPI
```bash
pip install peak-acl
```

---

## Quick Start

### Parse an ACL string
```python
from peak_acl import parse

raw = "(inform :content \"hello\" :sender (agent-identifier :name alice :addresses (sequence)) )"
msg = parse(raw)
print(msg.performative_upper)  # INFORM
print(msg['content'])          # "hello"
```

### Serialize an `AclMessage`
```python
from peak_acl.message.acl import AclMessage
from peak_acl.serialize import dumps

m = AclMessage(
    performative="request",
    content="(do-something)",
    language="fipa-sl0",
)
print(dumps(m))
```

### Send over HTTP-MTP
```python
from peak_acl.transport.http_client import HttpMtpClient
from peak_acl.message.aid import AgentIdentifier
from peak_acl.message.acl import AclMessage

sender = AgentIdentifier("me@platform", ["http://localhost:7777/acc"])
receiver = AgentIdentifier("df@platform", ["http://remote-host:7777/acc"])
acl = AclMessage(performative="inform", content="hi")

async def main():
    async with HttpMtpClient() as client:
        await client.send(receiver, sender, acl, receiver.addresses[0])
```

### Run an inbound HTTP-MTP server
```python
import asyncio
from peak_acl.transport.http_mtp import start_server

async def on_message(env, acl):
    print("IN:", env.from_.name, acl.performative_upper)

async def main():
    server, runner, site = await start_server(on_message=on_message, port=7777)
    await asyncio.Event().wait()  # keep running

asyncio.run(main())
```

---

## Working with SL0 / DF Helpers
The module `peak_acl.sl0` offers a small AST + serializer/parser for FIPA-SL0, enough to talk to JADE's DF/AMS:

```python
from peak_acl import sl0
from peak_acl.message.aid import AgentIdentifier

my = AgentIdentifier("agent@platform", ["http://localhost:7777/acc"])
df = AgentIdentifier("df@platform", ["http://host:7777/acc"])

content = sl0.build_register_content(my, [("my-service", "type")], df=df)
print(content)
```

Higher-level convenience wrappers live in `peak_acl.df_manager` (register, deregister, search, decode replies).

---

## Conversation Manager
`ConversationManager` implements the typical FIPA-Request flow. You provide a low-level `send_fn` and it gives you a `Future` that resolves when the conversation ends.

```python
from peak_acl.conversation import ConversationManager

async def send_fn(msg, url):
    ...  # your transport

cm = ConversationManager(send_fn)
future = await cm.send_request(sender=..., receiver=..., content="(foo)")
reply_msg = await future  # INFORM / FAILURE / REFUSE
```

It also supports optional timeouts.

---

## Events & Routing
`peak_acl.router.classify_message` inspects an incoming `(Envelope, AclMessage)` pair and returns a `(kind, payload)` tuple (e.g., `"df-result"`, list of `AgentDescription`). See `peak_acl.event.Kind` for all kinds.

`InboundDispatcher` + `MessageTemplate` allow pattern-based callbacks for incoming ACLs.

---

## Documentation
HTML API documentation is generated with **Sphinx** using the
[`furo`](https://github.com/pradyunsg/furo) theme. Install the optional
documentation dependencies and build it locally:

```bash
pip install -e .[docs]
make -C docs html
```

The resulting site will be available under `docs/_build/html/index.html`.

---

## Roadmap
- Integrate richer SL (beyond SL0) AST/visitor support.
- Optional IPv6-aware network utils.
- More exhaustive error handling/typing for user-defined params.
- Sphinx documentation site (autodoc from current docstrings).

---

## Contributing
Pull requests are welcome! For substantial changes, open a discussion first.

- Format code with **black** and **isort**.
- Run tests with **pytest** (async tests use pytest-asyncio).
- Follow Conventional Commits if possible (e.g., `feat:`, `fix:`).

---

## License
`peak-acl` is **free and open-source** software. See the `LICENSE` file for full text.

