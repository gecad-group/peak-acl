# peak-acl: FIPA-ACL parser & transport helpers for PEAK

[![PyPI](https://img.shields.io/pypi/v/peak-acl)](https://pypi.org/project/peak-acl/)
[![Python Versions](https://img.shields.io/pypi/pyversions/peak-acl)](https://pypi.org/project/peak-acl/)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](../LICENSE)

`peak-acl` is a lightweight package that parses, builds and transports
[FIPA-ACL](https://www.fipa.org/specs/fipa00061/SC00061G.html) messages with
first-class support for JADE-compatible HTTP-MTP. It integrates with the
[PEAK](https://github.com/gecad-group/peak-mas) framework but can be used in any
Python project.

---

## Table of Contents
- [Features](#readme-features)
- [Prerequisites](#readme-prerequisites)
- [Installation](#readme-installation)
- [Quick Start](#readme-quick-start)
- [Working with SL0 / DF Helpers](#readme-working-with-sl0--df-helpers)
- [Conversation Manager](#readme-conversation-manager)
- [Events & Routing](#readme-events--routing)
- [Documentation](#readme-documentation)
- [Roadmap](#readme-roadmap)
- [Contributing](#readme-contributing)
- [License](#readme-license)

---

(readme-features)=
## Features
- ✅ **Full FIPA-ACL message model** (`performative`, `sender`, `receiver`, ...).
- ✅ **Dict-like access** on `AclMessage` (`msg["content"]`, `msg.get(...)`).
- ✅ **ANTLR-based FIPA-ACL parser** → `AclMessage` objects.
- ✅ **SL0 helpers** for Directory Facilitator interactions.
- ✅ **HTTP-MTP client & server** with automatic retries.
- ✅ **Conversation manager** implementing the FIPA-Request protocol.
- ✅ **Utilities** for message routing and async helpers.

---

(readme-prerequisites)=
## Prerequisites
- Python **>= 3.9**
- Optional: a JADE ACC or compatible HTTP-MTP endpoint.

Development requirements are provided under the `dev` extra (pytest, mypy, black, isort, ...).

---

(readme-installation)=
## Installation

```bash
pip install peak-acl
```
---

(readme-quick-start)=
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

(readme-working-with-sl0--df-helpers)=
## Working with SL0 / DF Helpers
`peak_acl.sl0` provides a minimal AST and serializer for FIPA-SL0 to talk to
JADE's DF/AMS.

---

(readme-conversation-manager)=
## Conversation Manager
`ConversationManager` helps implementing the FIPA-Request flow. Supply a
low-level `send_fn` and await the resulting `Future` for the reply.

---

(readme-events--routing)=
## Events & Routing
`InboundDispatcher` plus `MessageTemplate` allow pattern-based callbacks for
incoming ACLs. See `peak_acl.runtime.classify_message` for predefined kinds.

---

(readme-documentation)=
## Documentation
The project's full API and usage documentation is available within this Sphinx site
and online at the project's repository.

---

(readme-roadmap)=
## Roadmap
- Richer SL (beyond SL0) support.
- Optional IPv6-aware network utilities.
- Extended error handling for user-defined parameters.
- Sphinx documentation site populated from docstrings.

---

(readme-contributing)=
## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests on
GitHub.

---

(readme-license)=
## License
`peak-acl` is licensed under the GNU GPL v3. See the `LICENSE` file for
details.

