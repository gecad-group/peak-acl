SL0 / DF Helpers
================

When to use
-----------

Use the SL0 and Directory Facilitator helpers when your agent needs to
register with a DF or query it using FIPA-SL0 payloads. The helpers build
the required SL0 structures and send them via HTTP-MTP.

Example
-------

.. code-block:: python

   from peak_acl.message import AgentIdentifier
   from peak_acl.transport import HttpMtpClient
   from peak_acl.runtime import df_manager

   my = AgentIdentifier("me@host", ["http://localhost:7777/acc"])
   df = AgentIdentifier("df@host", ["http://localhost:7777/acc"])

   async def main():
       async with HttpMtpClient() as http:
           await df_manager.register(
               my_aid=my,
               df_aid=df,
               services=[("echo", "utility")],
               http_client=http,
           )

Related APIs
------------

* :func:`~peak_acl.runtime.df_manager.register`
* :func:`~peak_acl.runtime.df_manager.search_services`
* :func:`~peak_acl.runtime.df_manager.decode_df_reply`
* :mod:`peak_acl.sl`

