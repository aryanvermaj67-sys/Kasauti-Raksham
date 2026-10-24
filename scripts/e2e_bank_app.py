"""Drive the bank app through the full demo-001 flow in a real browser, against the running backend.

Usage: python scripts/e2e_bank_app.py --lang en|hi [--demo demo-001|demo-002|demo-003] [--offline] [--base http://localhost:5173]
Needs the backend on :8000 and the frontend on :5173. Prints the visible result text and saves screenshots to
docs/screens/. --offline aborts every browser request that is not to localhost (fonts, CDNs, anything) and
fails if one was attempted; it also checks that the backend is in LLM_PROVIDER=cache mode.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SCREENS = ROOT / "docs" / "screens"
LOCAL = {"localhost", "127.0.0.1"}


def backend_in_cache_mode(base):
    """An image that is not in the cache must give 404 in cache mode (offline mode would OCR it instead)."""
    boundary = uuid.uuid4().hex
    png = b"\x89PNG\r\n\x1a\n" + uuid.uuid4().bytes
    body = (
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="x.png"\r\n'
            f"Content-Type: image/png\r\n\r\n"
        ).encode()
        + png
        + f"\r\n--{boundary}--\r\n".encode()
    )
    req = urllib.request.Request(
        f"{base}/api/read", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    try:
        urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as e:
        return e.code == 404 and "no cached ClaimSet" in json.loads(e.read())["detail"]
    return False


# what each demo's FR-8.4 screen must show; demo-001 keeps its original screenshot names
EXPECT = {"demo-001": "CONTRADICTS", "demo-002": "MATCHES", "demo-003": "NO_RECORD"}


def check_screen(expect, ui, text, count):
    """FR-8.4 per outcome. Texts come from the same template file the UI uses."""
    has = lambda key: ui[key] in text  # noqa: E731
    if expect == "MATCHES":
        return {
            "confirmation shown": has("matches_note"),
            "no alert (no 'does not match' row)": not has("outcome_CONTRADICTS"),
            "no complaint / 1930 button": count("complaint") == 0 and not has("report_1930"),
            "no trusted contact, no callback": count("act-trusted_contact") == count("act-bank_callback") == 0,
        }
    if expect == "NO_RECORD":
        return {
            "'we could not verify this' shown": has("no_record_title"),
            "self-checks: CDSL easi, monthly CAS, SEBI Check": all(
                has(k) for k in ("self_check_cdsl", "self_check_cas", "self_check_sebi")
            ),
            "optional bank callback offered": count("act-bank_callback") == 1,
            "no complaint, no trusted contact": count("complaint") == count("act-trusted_contact") == 0,
        }
    return {
        "complaint text pre-filled": count("complaint") == 1,
        "trusted contact and callback offered": count("act-trusted_contact") == count("act-bank_callback") == 1,
    }


def run(lang, offline, base, demo, video=None):
    SCREENS.mkdir(parents=True, exist_ok=True)
    customer = json.loads((ROOT / "data" / "demo_cache" / "demo_customers.json").read_text())[f"{demo}.png"]
    messages = json.loads(
        (ROOT / "backend" / "app" / "templates" / f"messages_{lang}.json").read_text(encoding="utf-8")
    )
    ui = messages["ui"]
    tag = (lang if demo == "demo-001" else f"{demo}_{lang}") if not video else f"video_{lang}"
    external = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 430, "height": 900})
        if offline:

            def guard(route):
                if urlparse(route.request.url).hostname in LOCAL:
                    return route.continue_()
                external.append(route.request.url)
                return route.abort()

            page.route("**/*", guard)
        page.goto(f"{base}/app?customer={customer}")
        if lang == "hi":
            page.click("[data-testid=lang-toggle]")
        page.click("[data-testid=check-button]")
        page.set_input_files("[data-testid=shot-input]", str(ROOT / "data" / "demo_cache" / f"{demo}.png"))
        if video:
            page.set_input_files("[data-testid=video-input]", str(ROOT / video))
        page.click("[data-testid=read-button]")
        page.wait_for_selector("[data-testid=confirm]", timeout=120000)
        if video:
            page.fill("[data-testid=field-endorsement-person]", "DEV clip speaker")
        page.wait_for_function("!document.querySelector('[data-testid=continue]').disabled")
        page.screenshot(path=str(SCREENS / f"confirm_{tag}.png"), full_page=True)
        page.click("[data-testid=continue]")
        page.fill("[data-testid=otp]", "123456")
        page.screenshot(path=str(SCREENS / f"consent_{tag}.png"), full_page=True)
        page.click("[data-testid=approve]")
        page.click("[data-testid=step-checking] [data-testid=next]", timeout=60000)  # enabled once records are loaded
        page.wait_for_selector("[data-testid=result]", timeout=60000)
        text = page.inner_text("[data-testid=result]")
        page.click("[data-testid=result] [data-testid=next]")  # the Action step holds the complaint and buttons
        page.wait_for_selector("[data-testid=actions]")
        checks = check_screen(EXPECT[demo], ui, text, lambda tid: page.locator(f"[data-testid={tid}]").count())
        if video:  # the record column's fixed words before the {time_ranges} parameter
            changed = messages["reason_codes"]["ENDORSEMENT_WORDS_CHANGED"]["record"].split("{")[0].strip()
            checks["video finding shown (words changed, with time range)"] = changed in text
        complaint = page.input_value("[data-testid=complaint]") if EXPECT[demo] == "CONTRADICTS" else ""
        page.click("[data-testid=act-still_pay]")
        page.wait_for_selector(f"text={ui['still_pay_note']}")
        checks["'I still want to pay' recorded, payment not blocked"] = True
        text += "\n" + page.inner_text("[data-testid=actions]")
        # the bundled face this language's body text uses: Inter for English, Noto Sans Devanagari for Hindi
        face, sample = ("Noto Sans Devanagari", "हिंदी") if lang == "hi" else ("Inter", "Kasauti")
        fonts = page.evaluate(f"document.fonts.check('16px \"{face}\"', '{sample}')")
        page.screenshot(path=str(SCREENS / f"result_{tag}.png"), full_page=True)
        browser.close()
    print(f"=== {demo} ({customer}) visible result text ({lang}{', offline' if offline else ''}) ===\n{text}\n")
    if complaint:
        print(f"=== complaint text ===\n{complaint}\n")
    checks[f"bundled font {face} loaded"] = fonts
    if offline:
        checks["backend in LLM_PROVIDER=cache"] = backend_in_cache_mode("http://localhost:8000")
        checks[f"no non-localhost requests ({len(external)})"] = not external
    for name, ok in checks.items():
        print(f"  [{'ok' if ok else 'FAIL'}] {EXPECT[demo]}: {name}")
    print(f"screenshots: docs/screens/*_{tag}.png")
    passed = all(checks.values())
    print("PASSED" if passed else "FAILED")
    return 0 if passed else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["en", "hi"], default="en")
    ap.add_argument("--demo", choices=sorted(EXPECT), default="demo-001")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--video", help="also upload this clip, e.g. data/media/fakes/dev_01_fake.mp4")
    ap.add_argument("--base", default="http://localhost:5173")
    a = ap.parse_args()
    sys.exit(run(a.lang, a.offline, a.base, a.demo, a.video))
