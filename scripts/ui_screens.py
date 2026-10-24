"""Screenshot all 8 customer-app steps for every demo scenario in English and Hindi, with the network blocked.

Usage: python scripts/ui_screens.py   (backend on :8000 in LLM_PROVIDER=cache, frontend on :5173)
Saves docs/screens/ui/<scenario>_<lang>_<n>_<step>.png. Fails if any non-localhost request is attempted, or if any
visible character on a Hindi screen draws as the font's "missing glyph" box.
"""

import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screens" / "ui"
APP = "http://localhost:5173"
STEPS = ["payment", "upload", "confirm", "consent", "checking", "result", "action", "pack"]
# characters that draw like an unassigned code point have no glyph in the page's fonts
TOFU = """() => {
  const chars = [...new Set([...document.body.innerText].filter((c) => c.trim()))]
  const c = document.createElement('canvas'); c.width = 48; c.height = 48
  const g = c.getContext('2d'); const font = getComputedStyle(document.body).fontFamily
  const draw = (ch) => {
    g.clearRect(0, 0, 48, 48); g.font = `28px ${font}`; g.fillText(ch, 6, 36)
    return g.getImageData(0, 0, 48, 48).data.join()
  }
  const missing = draw('\\u0378')
  return chars.filter((ch) => draw(ch) === missing)
}"""


def run_one(browser, s: dict, lang: str, blocked: list, tofu: dict) -> int:
    """One scenario in one language through all 8 steps; returns the number of screenshots taken."""
    page = browser.new_page(viewport={"width": 430, "height": 900}, accept_downloads=True)

    def guard(route):
        if urlparse(route.request.url).hostname in {"localhost", "127.0.0.1"}:
            return route.continue_()
        blocked.append(route.request.url)
        return route.abort()

    page.route("**/*", guard)

    def snap(n):
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(OUT / f"{s['id']}_{lang}_{n + 1}_{STEPS[n]}.png"), full_page=True)
        if lang == "hi":
            tofu[f"{s['id']} {STEPS[n]}"] = page.evaluate(TOFU)

    page.goto(f"{APP}/app")
    page.wait_for_selector("[data-testid=status-chip][data-status=ready]", timeout=300000)
    page.click(f"[data-testid=scenario-{s['id']}]")
    if lang == "hi":
        page.click("[data-testid=lang-toggle]")
    snap(0)
    page.click("[data-testid=check-button]")
    page.click("[data-testid=use-scenario]")
    page.wait_for_function("!document.querySelector('[data-testid=read-button]').disabled")
    snap(1)
    page.click("[data-testid=read-button]")
    page.wait_for_selector("[data-testid=confirm]", timeout=120000)
    if page.locator("[data-testid=field-endorsement-person]").count():
        page.fill("[data-testid=field-endorsement-person]", "DEV clip speaker")
    page.wait_for_function("!document.querySelector('[data-testid=continue]').disabled")
    snap(2)
    page.click("[data-testid=continue]")
    page.fill("[data-testid=otp]", "123456")
    snap(3)
    page.click("[data-testid=approve]")
    page.wait_for_selector("[data-testid=record-sources]", timeout=60000)
    snap(4)
    page.click("[data-testid=step-checking] [data-testid=next]")
    page.wait_for_selector("[data-testid=result]")
    snap(5)
    page.click("[data-testid=result] [data-testid=next]")
    snap(6)
    page.click("[data-testid=actions] [data-testid=next]")
    with page.expect_download() as dl:
        page.click("[data-testid=pack-download]")
    page.wait_for_selector("[data-testid=pack-info]")
    print(f"{s['id']} {lang}: {dl.value.suggested_filename}; {page.inner_text('[data-testid=pack-hash]')}")
    snap(7)
    page.close()
    return len(STEPS)


def guarded_page(browser, blocked: list):
    page = browser.new_page(viewport={"width": 1440, "height": 1000})

    def guard(route):
        if urlparse(route.request.url).hostname in {"localhost", "127.0.0.1"}:
            return route.continue_()
        blocked.append(route.request.url)
        return route.abort()

    page.route("**/*", guard)
    return page


def console_and_present(browser, lang: str, blocked: list, tofu: dict) -> int:
    """/reviewer with the newest case open, and /present after a real presenter run, in one language."""
    page = guarded_page(browser, blocked)
    page.goto(f"{APP}/reviewer?lang={lang}")
    page.wait_for_selector("[data-testid=stats]", timeout=60000)
    page.click("[data-testid^=queue-chk-]")
    page.wait_for_selector("[data-testid=matrix]")
    page.screenshot(path=str(OUT / f"reviewer_{lang}.png"), full_page=True)
    if lang == "hi":
        tofu["reviewer"] = page.evaluate(TOFU)
    page.goto(f"{APP}/present")
    if lang == "hi":
        page.click("[data-testid=present-lang]")
    page.click("[data-testid=present-run-demo-001]")
    page.wait_for_selector("[data-testid=present-note]", timeout=120000)
    page.frame_locator("[data-testid=present-console]").locator("[data-testid=stats]").wait_for(timeout=60000)
    page.frame_locator("[data-testid=present-phone]").locator("[data-testid=step-payment]").wait_for(timeout=60000)
    page.screenshot(path=str(OUT / f"present_{lang}.png"), full_page=True)
    print(f"present {lang}: {page.inner_text('[data-testid=present-note]')}")
    page.close()
    return 2


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    url = "http://localhost:8000/demo/scenarios"
    scenarios = json.loads(urllib.request.urlopen(url, timeout=10).read())["scenarios"]
    blocked, tofu, shots = [], {}, 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for s in scenarios:
            for lang in ("en", "hi"):
                shots += run_one(browser, s, lang, blocked, tofu)
        for lang in ("en", "hi"):
            shots += console_and_present(browser, lang, blocked, tofu)
        browser.close()
    bad = {k: v for k, v in tofu.items() if v}
    print(f"screenshots: {shots} in {OUT.relative_to(ROOT)}")
    print(f"blocked non-localhost requests: {len(blocked)} {blocked[:3]}")
    print(f"Hindi screens with missing-glyph boxes: {len(bad)} of {len(tofu)} {bad}")
    ok = shots == len(scenarios) * 2 * len(STEPS) + 4 and not blocked and not bad
    print("UI screens PASSED" if ok else "UI screens FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
