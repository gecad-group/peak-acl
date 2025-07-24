# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

# peak_acl/util/net.py
"""
Small networking utilities.

Currently provides :func:`discover_ip`, which returns the local routable IPv4
address by opening a UDP socket to a public endpoint (8.8.8.8:80). No packets
are actually sent; the OS chooses the outbound interface and we read that local
address. If that fails, a best-effort hostname lookup is used, finally falling
back to ``127.0.0.1``.
"""

from __future__ import annotations

import socket

__all__ = ["discover_ip"]


# --------------------------------------------------------------------------- #
# discover_ip
# --------------------------------------------------------------------------- #
def discover_ip() -> str:
    """Return the local routable IPv4 address (best effort).

    Strategy
    --------
    1. Create a UDP socket and ``connect()`` it to 8.8.8.8:80 so the kernel
       picks an outbound interface; read the local address via ``getsockname()``.
    2. On failure (no network, permission issues), try ``gethostbyname(gethostname())``.
    3. As a last resort, return ``"127.0.0.1"``.

    Returns
    -------
    str
        Dotted-quad IPv4 address.

    Notes
    -----
    * No packet is actually transmitted during step 1.
    * IPv6-only environments are not covered; consider adding an IPv6 variant
      if needed.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        # Fallback if the connect()/getsockname() path fails (e.g., offline box)
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"  # Final fallback to localhost
    finally:
        s.close()
