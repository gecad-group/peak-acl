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

# src/peak_acl/types.py
"""
Lightweight marker type for strings that must remain quoted during serialization.

``QuotedStr`` subclasses :class:`str` and is used by the serializer to
distinguish values that originally came from an ACL STRING token and therefore
need to keep quotes when emitted by ``dumps()``.
"""


class QuotedStr(str):
    """Marker for values parsed from STRING tokens that should stay quoted."""
    pass
