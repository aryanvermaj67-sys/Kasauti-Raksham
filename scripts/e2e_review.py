"""End to end: a customer check, a reviewer approval, the payee in the MOCK registry, and another payer warned.

Usage: python scripts/e2e_review.py   (backend on :8000, frontend on :5173)
Runtime approvals and acknowledgements from earlier runs are moved aside to *.bak first, so the run starts clean.
Screenshots: docs/screens/reviewer_en.png, evidence_pack.png, trigger_warning_en.png.
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "data" / "runtime"
SCREENS = ROOT / "docs" / "screens"
APP, API = "http://localhost:5173", "http://localhost:8000"
PAYEE = "zyphrastock.invest@mockupi"


def registry_hit(identifier):
    url = f"{API}/api/registry/lookup?identifier={urllib.parse.quote(identifier)}"
    return json.loads(urllib.request.urlopen(url, timeout=30).read())["payload"]["hit"]


def step(n, text):
    print(f"\n[step {n}] {text}")


def main():
    for name in ("suspect_registry_additions.json", "trigger_acks.json"):
        if (RUNTIME / name).exists():
            (RUNTIME / name).replace(RUNTIME / f"{name}.bak")
            print(f"moved aside earlier runtime state: data/runtime/{name} -> {name}.bak")
    other = json.loads((ROOT / "data" / "synthetic" / "ledger.json").read_text(encoding="utf-8"))[
        "demo_payee_customers"
    ][0]
    ok = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 430, "height": 900})

        step(1, "customer SYN-C0001 checks demo-001 with the fake video dev_01_fake.mp4")
        page.goto(f"{APP}/app?customer=SYN-C0001")
        page.click("[data-testid=check-button]")
        page.set_input_files("[data-testid=shot-input]", str(ROOT / "data" / "demo_cache" / "demo-001.png"))
        page.set_input_files("[data-testid=video-input]", str(ROOT / "data" / "media" / "fakes" / "dev_01_fake.mp4"))
        page.click("[data-testid=read-button]")
        page.wait_for_selector("[data-testid=confirm]", timeout=120000)
        page.fill("[data-testid=field-endorsement-person]", "DEV clip speaker")
        page.wait_for_function("!document.querySelector('[data-testid=continue]').disabled")
        page.click("[data-testid=continue]")
        page.fill("[data-testid=otp]", "123456")
        page.click("[data-testid=approve]")
        page.wait_for_selector("[data-testid=complaint]", timeout=60000)
        complaint = page.input_value("[data-testid=complaint]")
        check_id = re.search(r"chk-[0-9a-f]{12}", complaint)[0]
        print(f"check {check_id}; pre-filled 1930 complaint:\n  {complaint}")
        ok["complaint names the video clip, the changed range and the pack"] = all(
            s in complaint for s in ("dev_01.mp4", "0:11-0:13", f"pack-{check_id}")
        )

        step(2, f"before review: is {PAYEE} in the MOCK Suspect Registry?")
        before = registry_hit(PAYEE)
        print(f"  registry hit: {before}")
        ok["one report alone does not list the payee"] = before is None
        page.goto(f"{APP}/app?customer={other}")
        page.wait_for_load_state("networkidle")
        warned = page.locator("[data-testid=trigger-banner]").count() == 1
        print(f"  {other} (paid {PAYEE} earlier) sees a warning: {warned}")
        ok["no warning before approval"] = not warned

        step(3, "reviewer opens the queue, reads the evidence and approves")
        page.set_viewport_size({"width": 1100, "height": 900})
        page.goto(f"{APP}/reviewer")
        page.click(f"[data-testid=queue-{check_id}]")
        chain = page.inner_text("[data-testid=chain-status]")
        print(f"  {chain}")
        page.fill("[data-testid=reason]", "screenshot holdings and broker contradict the record; video words changed")
        page.click("[data-testid=approve]")
        page.wait_for_selector("[data-testid=review-outcome]")
        approved = page.inner_text("[data-testid=review-outcome]")
        print(f"  {approved}")
        page.click("[data-testid=export-pack]")
        page.wait_for_function(
            "document.querySelector('[data-testid=review-outcome]').innerText.includes('Evidence pack')"
        )
        exported = page.inner_text("[data-testid=review-outcome]")
        print(f"  {exported}")
        page.screenshot(path=str(SCREENS / "reviewer_en.png"), full_page=True)
        ok["chain intact before approval"] = "intact" in chain
        ok["approval lists other payers"] = other in approved

        step(4, "evidence pack HTML")
        html = Path(re.search(r"written: (.+\.html)", exported)[1])
        print(f"  JSON: {html.with_suffix('.json')}\n  HTML: {html}")
        page.goto(html.as_uri())
        print(f"  {page.inner_text('p.ok, p.bad')}")
        page.screenshot(path=str(SCREENS / "evidence_pack.png"), full_page=True)
        ok["pack says hash listing, chain PASSED"] = (
            "Hash listing to support a certificate" in page.content() and "PASSED" in page.content()
        )

        step(5, f"after review: is {PAYEE} in the MOCK Suspect Registry?")
        after = registry_hit(PAYEE)
        print(f"  registry hit: {after}")
        ok["payee listed after approval"] = bool(after) and after["check_id"] == check_id

        step(6, f"another customer, {other}, who paid {PAYEE} earlier, opens the bank app")
        page.set_viewport_size({"width": 430, "height": 900})
        page.goto(f"{APP}/app?customer={other}")
        page.wait_for_selector("[data-testid=trigger-banner]")
        warning = page.inner_text("[data-testid=trigger-banner]")
        print("  " + warning.replace("\n", "\n  "))
        page.screenshot(path=str(SCREENS / "trigger_warning_en.png"), full_page=True)
        ok["other payer warned, payment not blocked"] = PAYEE in warning
        browser.close()
    print()
    for name, good in ok.items():
        print(f"  [{'ok' if good else 'FAIL'}] {name}")
    print("PASSED" if all(ok.values()) else "FAILED")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
