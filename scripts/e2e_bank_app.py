"""Drive the bank app through the full demo-001 flow in a real browser, against the running backend.

Usage: python scripts/e2e_bank_app.py --lang en|hi [--offline] [--base http://localhost:5173]
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
DEMO = ROOT / "data" / "demo_cache" / "demo-001.png"
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


def run(lang, offline, base):
    SCREENS.mkdir(parents=True, exist_ok=True)
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
        page.goto(f"{base}/app")
        if lang == "hi":
            page.click("[data-testid=lang-toggle]")
        page.click("[data-testid=check-button]")
        page.set_input_files("[data-testid=shot-input]", str(DEMO))
        page.click("[data-testid=read-button]")
        page.wait_for_selector("[data-testid=confirm]")
        page.wait_for_function("!document.querySelector('[data-testid=continue]').disabled")
        page.screenshot(path=str(SCREENS / f"confirm_{lang}.png"), full_page=True)
        page.click("[data-testid=continue]")
        page.fill("[data-testid=otp]", "123456")
        page.screenshot(path=str(SCREENS / f"consent_{lang}.png"), full_page=True)
        page.click("[data-testid=approve]")
        page.wait_for_selector("[data-testid=result]", timeout=60000)
        page.click("[data-testid=act-trusted_contact]")
        page.wait_for_function("document.querySelector('[data-testid=actions]').innerText.includes('MOCK')")
        text = page.inner_text("[data-testid=result]")
        complaint = page.input_value("[data-testid=complaint]")
        fonts = page.evaluate("document.fonts.check('16px \"Noto Sans Devanagari\"', 'हिंदी')")
        page.screenshot(path=str(SCREENS / f"result_{lang}.png"), full_page=True)
        browser.close()
    print(f"=== visible result text ({lang}{', offline' if offline else ''}) ===\n{text}\n")
    print(f"=== complaint text ===\n{complaint}\n")
    print(f"Noto Sans Devanagari loaded: {fonts}; screenshots: docs/screens/*_{lang}.png")
    ok = fonts and "1930" in text and complaint
    if offline:
        cache = backend_in_cache_mode("http://localhost:8000")
        print(f"backend LLM_PROVIDER=cache: {cache}; non-localhost requests attempted: {len(external)} {external}")
        ok = ok and cache and not external
    print("PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["en", "hi"], default="en")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--base", default="http://localhost:5173")
    a = ap.parse_args()
    sys.exit(run(a.lang, a.offline, a.base))
