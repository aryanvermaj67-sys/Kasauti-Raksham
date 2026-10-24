"""Reset the demo to a clean state: evidence DB and dev key, MOCK registry additions, trigger acks, event log.

Usage: python scripts/reset_demo.py   (or scripts/reset_demo.sh / reset_demo.ps1). Stop the backend first.
If .env has no EVIDENCE_KEY, one is generated and written there (.env is git-ignored); evidence encrypted
under the old key could no longer be read, which is one more reason the reset clears it.
"""

import subprocess
import sys
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app import demo_reset  # noqa: E402

ENV = ROOT / ".env"
SEED = "data/synthetic/suspect_registry_mock.json"


def ensure_key() -> None:
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    if any(line.startswith("EVIDENCE_KEY=") and line.split("=", 1)[1].strip() for line in lines):
        print("EVIDENCE_KEY: present in .env (kept)")
        return
    lines = [line for line in lines if not line.startswith("EVIDENCE_KEY=")]
    ENV.write_text("\n".join([*lines, f"EVIDENCE_KEY={Fernet.generate_key().decode()}"]) + "\n", encoding="utf-8")
    print("EVIDENCE_KEY: none in .env, generated a new one and wrote it to .env (git-ignored)")


def main() -> int:
    before = demo_reset.counts()
    ensure_key()
    # the seed file is committed and never written by the app; restore it if someone edited it by hand
    if subprocess.run(["git", "diff", "--quiet", "--", SEED], cwd=ROOT).returncode:
        subprocess.run(["git", "checkout", "--", SEED], cwd=ROOT, check=True)
        print(f"restored {SEED} from git")
    demo_reset.reset()
    after = demo_reset.counts()
    print(f"{'':32}{'before':>8}{'after':>8}")
    for k in before:
        print(f"{k:32}{before[k]:>8}{after[k]:>8}")
    clean = all(after[k] == 0 for k in after if k != "registry seed entries (mock)")
    print("reset OK" if clean else "reset FAILED")
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
