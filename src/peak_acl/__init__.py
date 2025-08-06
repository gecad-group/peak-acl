# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 Santiago Bossa
#
# This file is part of peak-acl.
#
# peak-acl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# peak-acl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with peak-acl.  If not, see the LICENSE file in the project root.

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
from .parser import parse
from .message.acl import AclMessage
from .message.serialize import dumps

__all__: list[str] = ["parse", "AclMessage", "dumps", "__version__"]

# --------------------------------------------------------------------------- #
# Version
# --------------------------------------------------------------------------- #
try:
    __version__: str = _version("peak-acl")
except PackageNotFoundError:
    __version__ = "0.0.0"
