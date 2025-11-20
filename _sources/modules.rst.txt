API Reference
=============

Runtime Components
------------------

Core utilities for running an agent, handling conversations and
dispatching inbound messages.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   peak_acl.runtime.content
   peak_acl.runtime.conversation
   peak_acl.runtime.df_manager
   peak_acl.runtime.dispatcher
   peak_acl.runtime.event
   peak_acl.runtime.message_template
   peak_acl.runtime.router
   peak_acl.runtime.runtime

Semantic Language (SL)
----------------------

Helpers for parsing, serializing and manipulating FIPA Semantic Language
constructs including the Agent Management ontology.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   peak_acl.sl.fipa_am
   peak_acl.sl.sl0
   peak_acl.sl.sl_parser
   peak_acl.sl.sl_visitor

Parser Utilities
----------------

Functions and visitors that translate raw ACL strings into Python objects.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   peak_acl.parser.parse
   peak_acl.parser.parse_helpers
   peak_acl.parser.types
   peak_acl.parser.visitor

Message Models
--------------

In-memory representations of ACL messages, envelopes and serialization
helpers.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   peak_acl.message.acl
   peak_acl.message.aid
   peak_acl.message.envelope
   peak_acl.message.serialize

Transport Layer
---------------

HTTP-based Message Transport Protocol implementations and multipart helpers.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   peak_acl.transport
   peak_acl.transport.http_client
   peak_acl.transport.http_mtp
   peak_acl.transport.multipart

Utility Helpers
---------------

Miscellaneous asynchronous and networking utilities used throughout the
project.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   peak_acl.util.async_utils
   peak_acl.util.net
