Events & Routing
================

When to use
-----------

Use the dispatcher and router when you want to route incoming messages to
callbacks based on their contents and classify them as DF replies or
external messages.

Example
-------

.. code-block:: python

   from peak_acl.runtime.dispatcher import InboundDispatcher
   from peak_acl.runtime.message_template import MessageTemplate
   from peak_acl.runtime.router import classify_message

   dispatcher = InboundDispatcher()

   async def handle_inform(sender, acl):
       print("inform:", acl.get("content"))

   dispatcher.add(MessageTemplate(performative="inform"), handle_inform)

   # inside your transport receive loop
   # kind, payload = classify_message(env, acl, df_aid)
   # await dispatcher.dispatch(env.from_, acl)

Related APIs
------------

* :class:`~peak_acl.runtime.dispatcher.InboundDispatcher`
* :class:`~peak_acl.runtime.message_template.MessageTemplate`
* :func:`~peak_acl.runtime.router.classify_message`
* :mod:`peak_acl.runtime.event`

