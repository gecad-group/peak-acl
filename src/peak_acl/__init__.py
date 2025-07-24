# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

"""
peak_acl
========
FIPA-ACL parser and transport helpers for the PEAK framework.

Exports
-------
- :func:`parse` – converts ACL strings into :class:`AclMessage`
- :class:`AclMessage` – in-memory ACL message model
- :func:`dumps` – serialize :class:`AclMessage` to FIPA-ACL string
- ``__version__`` – package version (PEP 440), fallback ``"0.0.0"``
"""

from importlib.metadata import version as _version, PackageNotFoundError

# --------------------------------------------------------------------------- #
# Public API re-exports
# --------------------------------------------------------------------------- #
from .parse import parse
from .message.acl import AclMessage
from .serialize import dumps

__all__: list[str] = ["parse", "AclMessage", "dumps", "__version__"]

# --------------------------------------------------------------------------- #
# Version
# --------------------------------------------------------------------------- #
try:
    __version__: str = _version("peak-acl")
except PackageNotFoundError:
    __version__ = "0.0.0"
