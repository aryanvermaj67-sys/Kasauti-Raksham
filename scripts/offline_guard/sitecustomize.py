"""Loaded by the demo backend via PYTHONPATH: any non-loopback socket connection fails and is logged.

This proves the backend needs no network. It does not switch off Wi-Fi; do that by hand for the final rehearsal.
"""

import socket
import sys

_connect = socket.socket.connect
LOOPBACK = ("127.", "::1", "localhost", "0.0.0.0")


def _guarded(self, address):
    host = address[0] if isinstance(address, tuple) else str(address)
    if self.family in (socket.AF_INET, socket.AF_INET6) and not str(host).startswith(LOOPBACK):
        print(f"OFFLINE GUARD blocked connect to {address}", file=sys.stderr, flush=True)
        raise OSError(f"offline guard: network disabled ({address})")
    return _connect(self, address)


socket.socket.connect = _guarded
