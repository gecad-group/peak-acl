# MIT License
# Copyright (c) 2025 Santiago Bossa
# See LICENSE file in the project root for full license text.

# peak_acl/util/net.py
"""
Small networking utilities.

Currently provides :func:`discover_ip`, which returns the local routable IPv4
address by opening a UDP socket to a public endpoint (8.8.8.8:80). No packets
are actually sent; the OS chooses the outbound interface, and we read that
assigned local address.
"""

from __future__ import annotations

import socket

__all__ = ["discover_ip"]


# --------------------------------------------------------------------------- #
# discover_ip
# --------------------------------------------------------------------------- #
def discover_ip() -> str:
    """Return the local routable IPv4 address.

    This uses a common UDP trick: connect a datagram socket to 8.8.8.8:80 so
    the kernel selects the appropriate outgoing interface, then read the local
    address from ``getsockname()``. The socket is always closed.

    Returns
    -------
    str
        Dotted-quad IPv4 address (e.g., ``"192.168.1.34"``).

    Notes
    -----
    * No UDP packet is actually transmitted.
    * May raise ``OSError`` if networking is unavailable or blocked.
    * IPv6-only environments will still yield an IPv4 from the selected iface
      (or fail). Consider a future IPv6-aware variant if needed.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        #Fallback if the connection fails (e.g., no network)
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1" # Fallback to localhost
    finally:
        s.close()
