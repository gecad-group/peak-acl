Conversation Manager
====================

When to use
-----------

Use the conversation manager to handle FIPA-Request style conversations
where a request may produce multiple replies. It tracks conversation IDs
and resolves a future when the final INFORM or FAILURE arrives.

.. note::
   Make sure every inbound ACL is passed to
   :meth:`~peak_acl.runtime.conversation.ConversationManager.on_message` so
   pending conversations can progress.

Example
-------

.. code-block:: python

   from peak_acl.message import AgentIdentifier
   from peak_acl.runtime.conversation import ConversationManager
   from peak_acl.transport import HttpMtpClient

   me = AgentIdentifier("me@host", ["http://localhost:7777/acc"])
   you = AgentIdentifier("you@host", ["http://other:7777/acc"])

   async def main():
       async with HttpMtpClient() as http:

           async def send_fn(msg, url):
               # wrap HttpMtpClient.send to match ConversationManager signature
               await http.send(you, me, msg, url)

           cm = ConversationManager(send_fn)
           fut = await cm.send_request(
               sender=me,
               receiver=you,
               content="(ping)",
               url=you.addresses[0],
           )

           # elsewhere feed inbound ACLs to the manager
           # cm.on_message(inbound_acl)

           reply = await fut
           print("reply:", reply.performative_upper)

Related APIs
------------

* :class:`~peak_acl.runtime.conversation.ConversationManager`
* :meth:`~peak_acl.runtime.conversation.ConversationManager.send_request`
* :meth:`~peak_acl.runtime.conversation.ConversationManager.on_message`

