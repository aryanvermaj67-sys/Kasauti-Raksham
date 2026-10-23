"""Fetch or verify every public file listed in data/SOURCES.md.

Usage: python scripts/fetch_registries.py [--ip 202.191.181.158]
A file already on disk is checked against the SHA-256 in SOURCES.md (no network needed).
A missing file is downloaded if a script can fetch it, and its SOURCES.md row gets the date and
SHA-256. Files that need a person (browser-only or PDF-only) are reported as "manual download needed".
--ip is passed to fetch_sebi.py for laptops whose DNS cannot resolve sebi.gov.in.
Exit 1 if any file is missing or its hash differs from the log.
"""

import argparse
import hashlib
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "SOURCES.md"
REG = "data/registries/"
REBIT = "https://specifications.rebit.org.in/api_schema/account_aggregator/documentation/"
# SOURCES.md row name -> (local path, how: url | "sebi" | "manual: reason")
FILES = {
    "sebi_brokers.csv": (REG + "sebi_brokers.csv", "sebi"),
    "sebi_investment_advisers.csv": (REG + "sebi_investment_advisers.csv", "sebi"),
    "sebi_research_analysts.csv": (REG + "sebi_research_analysts.csv", "sebi"),
    "rbi_alert_list.csv": (
        REG + "rbi_alert_list.csv",
        "manual: RBI publishes the Alert List only as a PDF; typed by hand and kept in git",
    ),
    "nse_equity.csv": (REG + "nse_equity.csv", "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"),
    "bse_equity.csv": (
        REG + "bse_equity.csv",
        "manual: api.bseindia.com ListofScripData only answers a browser session; save it as CSV from a browser",
    ),
    "rebit_equities_schema": ("data/schemas/rebit_equities.html", REBIT + "equities.html"),
    "rebit_mutual_funds_schema": ("data/schemas/rebit_mutual_funds.html", REBIT + "mutual_funds.html"),
    "sahamati_fi_types_screenshot.png": (
        "docs/sources/sahamati_fi_types_screenshot.png",
        "manual: page screenshot, take it in a browser",
    ),
}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows():
    """SOURCES.md table rows keyed by the File cell; cells are [File, URL, Downloaded, By, SHA-256, Notes]."""
    out = {}
    for n, line in enumerate(LOG.read_text(encoding="utf-8").splitlines()):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| ") and len(cells) == 6:
            out[cells[0]] = (n, cells)
    return out


def write_row(name, **changes):
    lines = LOG.read_text(encoding="utf-8").splitlines()
    n, cells = rows()[name]
    for i, key in enumerate(["file", "url", "date", "by", "sha", "notes"]):
        cells[i] = changes.get(key, cells[i])
    lines[n] = "| " + " | ".join(cells) + " |"
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip")
    args = ap.parse_args()
    today = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%d %b %Y")
    log = rows()
    bad = 0
    for name, (rel, how) in FILES.items():
        path = ROOT / rel
        if name not in log:
            print(f"{name}: no row in SOURCES.md")
            bad += 1
            continue
        logged = log[name][1][4]
        if not path.exists():
            if how.startswith("manual:"):
                if "manual download needed" not in log[name][1][5]:
                    write_row(name, notes=f"manual download needed: {how[8:]}. {log[name][1][5]}".strip())
                print(f"{name}: manual download needed ({how[8:]})")
                bad += 1
                continue
            if how == "sebi":
                subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "fetch_sebi.py")] + (["--ip", args.ip] if args.ip else []),
                    check=True,
                )
            else:
                req = urllib.request.Request(how, headers=UA)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(urllib.request.urlopen(req, timeout=90).read())
            write_row(name, date=today, by="fetch_registries.py", sha=sha256(path))
            print(f"{name}: downloaded, sha256 {sha256(path)} logged")
            continue
        actual = sha256(path)
        if actual == logged:
            print(f"{name}: ok (sha256 matches log)")
        else:
            print(f"{name}: HASH DIFFERS from log ({actual} vs {logged or 'empty'}); re-log it if the source changed")
            bad += 1
    print(f"{len(FILES) - bad}/{len(FILES)} files present and matching the log")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
