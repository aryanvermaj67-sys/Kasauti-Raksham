"""Fetch SEBI recognised-intermediary lists (public) into data/registries/*.csv.

Usage: python scripts/fetch_sebi.py [--ip 202.191.181.158]
--ip pins www.sebi.gov.in to an address (curl --resolve) for networks whose DNS cannot resolve it.
Prints the SHA-256 of each file for data/SOURCES.md.
"""
import argparse
import csv
import hashlib
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HOST = "www.sebi.gov.in"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
LISTS = {  # intmId -> output file
    30: "sebi_brokers.csv",  # Registered Stock Brokers in equity segment
    13: "sebi_investment_advisers.csv",
    14: "sebi_research_analysts.csv",
}
OUT = Path(__file__).resolve().parent.parent / "data" / "registries"


def curl(args, ip, jar):
    cmd = ["curl", "-s", "-m", "90", "-A", UA, "-b", jar, "-c", jar]
    if ip:
        cmd += ["--resolve", f"{HOST}:443:{ip}"]
    return subprocess.run(cmd + args, capture_output=True, check=True).stdout.decode("utf-8", "replace")


def parse(page):
    """Each record is a run of card-view title/value pairs that starts at a 'Name' title."""
    pairs = re.findall(
        r"""<div class=["']title["']><span>\s*(.*?)\s*</span></div><div class=["']value[^"']*["']><span>(.*?)</span>""",
        page,
        re.S,
    )
    records, cur = [], None
    for k, v in pairs:
        k, v = html.unescape(k).strip(), " ".join(html.unescape(v).split())
        if k == "Name":
            cur = {}
            records.append(cur)
        if cur is not None:
            cur[k] = v
    return records


def fetch_list(intm_id, ip, jar):
    base = f"https://{HOST}/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId={intm_id}"
    first = curl([base], ip, jar)
    total = int(re.search(r"of (\d+) records", first).group(1))
    pages = -(-total // 25)
    rows = parse(first)
    for p in range(1, pages):
        body = (
            f"nextValue={p}&next=n&intmId={intm_id}&contPer=&name=&regNo=&email=&location=&exchange="
            f"&affiliate=&alp=&doDirect={p}&intmIds="
        )
        headers = ["-H", f"Origin: https://{HOST}", "-H", "X-Requested-With: XMLHttpRequest"]
        url = f"https://{HOST}/sebiweb/ajax/other/getintmfpiinfo.jsp"
        rows += parse(curl(["-e", base, *headers, "-d", body, url], ip, jar))
    return total, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip")
    ip = ap.parse_args().ip
    jar = str(Path(tempfile.gettempdir()) / "sebi_cookies.txt")
    for intm_id, fname in LISTS.items():
        total, rows = fetch_list(intm_id, ip, jar)
        if len(rows) != total:  # a short scrape must not be saved as if complete
            sys.exit(f"{fname}: expected {total} records, parsed {len(rows)}")
        cols = list(dict.fromkeys(k for r in rows for k in r))
        path = OUT / fname
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        print(fname, total, hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
