"""scripts/offline_guard (the demo backend's sitecustomize): any non-loopback connection raises; loopback works."""

import os
import subprocess
import sys

from tests.helpers import ROOT

CODE = """
import socket
srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
socket.create_connection(srv.getsockname(), timeout=2).close()
print("loopback ok")
for host in ("93.184.216.34", "8.8.8.8", "2001:4860:4860::8888"):
    try:
        socket.create_connection((host, 443), timeout=2)
        print("CONNECTED", host)
    except OSError as e:
        print("blocked", host, "offline guard" in str(e))
"""


def test_non_localhost_socket_connection_raises():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "scripts" / "offline_guard")}
    out = subprocess.run([sys.executable, "-c", CODE], env=env, capture_output=True, text=True, timeout=60).stdout
    print(out)
    assert "loopback ok" in out and "CONNECTED" not in out
    assert out.count("True") == 3  # each refusal came from the guard, not from a missing route
