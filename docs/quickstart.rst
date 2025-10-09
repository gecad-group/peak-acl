Quick Start
===========

#. **Install**

   Install the library to access helpers such as
   :func:`~peak_acl.parser.parse.parse` for converting ACL strings into
   :class:`~peak_acl.message.acl.AclMessage` objects.

   .. note::
      ``peak-acl`` requires Python 3.9 or newer.


#. **Parse a message**

   Convert a raw FIPA ACL string into an
   :class:`~peak_acl.message.acl.AclMessage` using
   :func:`~peak_acl.parser.parse.parse`.

   .. code-block:: python

      from peak_acl import parse

      raw = "(inform :content \"hello\")"
      msg = parse(raw)
      print(msg.performative_upper)
      print(msg["content"])

#. **Serialize a message**

   Build an :class:`~peak_acl.message.acl.AclMessage` and encode it back to
   a string with :func:`~peak_acl.message.serialize.dumps`.

   .. code-block:: python

      from peak_acl.message import AclMessage
      from peak_acl.message.serialize import dumps

      m = AclMessage(performative="request", content="(do-something)")
      print(dumps(m))

#. **Send over HTTP-MTP**

   Deliver a message to another agent via
   :class:`~peak_acl.transport.http_client.HttpMtpClient` using
   addresses defined by :class:`~peak_acl.message.aid.AgentIdentifier`.

   .. code-block:: python

      from peak_acl.transport import HttpMtpClient
      from peak_acl.message import AgentIdentifier, AclMessage

      sender = AgentIdentifier("me@host", ["http://localhost:7777/acc"])
      receiver = AgentIdentifier("df@host", ["http://other:7777/acc"])
      acl = AclMessage(performative="inform", content="hi")

      async def main():
         async with HttpMtpClient() as client:
            await client.send(receiver, sender, acl, receiver.addresses[0])

#. **Run an inbound HTTP-MTP server**

   Accept incoming messages by starting a listener with
   :func:`~peak_acl.transport.http_mtp.start_server`.

   .. warning::
      The server example below listens on all interfaces without
      authentication. Use it only in trusted environments.

   .. code-block:: python

      import asyncio
      from peak_acl.transport import start_server

      async def on_message(env, acl):
         print("IN:", env.from_.name, acl.performative_upper)

      async def main():
         await start_server(on_message=on_message, port=7777)
         await asyncio.Event().wait()

      asyncio.run(main())

