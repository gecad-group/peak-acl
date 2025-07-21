"""
peak_acl · FIPA-ACL parser and transport helpers for the PEAK framework.
"""

from importlib.metadata import version as _version, PackageNotFoundError

# ─────────────────────────── API pública ────────────────────────────

from .parse import parse
from .message.acl import AclMessage  


__all__: list[str] = [
    "parse",
    "AclMessage",
    "__version__",
]

__all__.append("dumps")


try:
    __version__: str = _version("peak-acl")
except PackageNotFoundError:
    __version__ = "0.0.0"
