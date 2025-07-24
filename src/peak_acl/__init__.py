# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

"""
peak_acl
========
FIPA-ACL parser and transport helpers for the PEAK framework.

Exports:
- :func:`parse` – parse ACL strings into :class:`AclMessage`
- :class:`AclMessage` – in-memory ACL message model
- ``__version__`` – package version (PEP 440), fallback "0.0.0"
"""

from importlib.metadata import version as _version, PackageNotFoundError

# --------------------------------------------------------------------------- #
# Public API re-exports
# --------------------------------------------------------------------------- #
from .parse import parse
from .message.acl import AclMessage

__all__: list[str] = ["parse", "AclMessage", "__version__"]

# NOTE: "dumps" is appended to __all__ but not imported here.
# If you intend to expose it, import from the correct module above.
__all__.append("dumps")

# --------------------------------------------------------------------------- #
# Version
# --------------------------------------------------------------------------- #
try:
    __version__: str = _version("peak-acl")
except PackageNotFoundError:
    __version__ = "0.0.0"
