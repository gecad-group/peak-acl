"""Miscellaneous utilities."""

from .async_utils import safe_create_task
from .net import discover_ip

__all__ = ["safe_create_task", "discover_ip"]
