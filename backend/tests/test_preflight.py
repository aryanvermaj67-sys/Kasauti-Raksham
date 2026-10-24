"""scripts/preflight.py: a port held by something that is not our server is NO-GO; a free port is fine."""

import importlib.util
import socket

from tests.helpers import ROOT

spec = importlib.util.spec_from_file_location("preflight", ROOT / "scripts" / "preflight.py")
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def test_port_held_by_a_silent_process_is_no_go():
    with socket.socket() as srv:
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        n = srv.getsockname()[1]
        ok, detail, fix = preflight.port(n, f"http://127.0.0.1:{n}/health")
        print(f"\nheld :{n} -> {ok} {detail}")
        assert not ok and fix
    ok, detail, _ = preflight.port(n, f"http://127.0.0.1:{n}/health")
    print(f"released :{n} -> {ok} {detail}")
    assert ok
