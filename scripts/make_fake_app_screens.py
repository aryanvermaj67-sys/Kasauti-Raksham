# ruff: noqa: E501  (the WORDS tables keep one language per few lines)
"""Make the fake-app screenshots (PRD data plan: ~60 images, 6 layouts, Hindi + English) with exact labels.

Usage: python -X utf8 scripts/make_fake_app_screens.py [--seed 7] [--score] [--score-dir DIR]
Writes data/media/fake_apps/fa01.png .. fa60.png and labels.json (git-ignored, regenerated from the seed).
Everything here is MOCK: invented firms, platforms and UPI handles (@mockupi / @validmock); listed company names are
public securities. A field an image does not show is null in its label. --score reads every image through the real
reader (POST /api/read, LLM_PROVIDER as set) and prints the fields it got wrong.
This set is for building and tuning; it is not data/frozen and never replaces it.
"""

import argparse
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
OUT = ROOT / "data" / "media" / "fake_apps"
EN, HI, BOLD = r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\Nirmala.ttc", r"C:\Windows\Fonts\arialbd.ttf"
W = 1080
SCREEN_H = 2340  # a full phone screen (9:19.5)
# listed companies, price band in rupees (an invented, rough band: only so quantity x price is a plausible value)
STOCKS = {
    "Reliance Industries Ltd": (1200, 1500), "Tata Consultancy Services Ltd": (3000, 4200), "Infosys Ltd": (1300, 1900),
    "HDFC Bank Ltd": (1400, 1800), "ICICI Bank Ltd": (1000, 1400), "State Bank of India": (700, 900),
    "Bharti Airtel Ltd": (1100, 1700), "Cipla Ltd": (1300, 1700), "Larsen & Toubro Ltd": (3000, 3900),
    "Maruti Suzuki India Ltd": (11000, 13500), "Sun Pharmaceutical Industries Ltd": (1400, 1900),
    "Asian Paints Ltd": (2200, 3000), "Bajaj Finance Ltd": (6500, 9000), "Axis Bank Ltd": (1000, 1300),
    "Hindustan Unilever Ltd": (2300, 2800), "Titan Company Ltd": (3000, 3900), "Wipro Ltd": (240, 320),
    "Hero MotoCorp Ltd": (4000, 5500), "Britannia Industries Ltd": (4500, 5800), "Coal India Ltd": (380, 480),
}  # fmt: skip
FIRMS = [
    "Zyphra Stock Club", "Orbit Gains Desk", "Silverline Capital Circle", "Nimbus Trade House",
    "Quantrix Growth Hub", "Falcon Alpha Traders", "Kiran Wealth Circle", "Sunrise Profit Club",
    "Meridian Stock Desk", "Vertex Returns Club",
]  # fmt: skip
PLATFORMS = [("Kubera Coin Exchange", "crypto"), ("Nimbal Trade Arena", "other"), ("Zenfx Markets", "forex"),
             ("Bitora Exchange", "crypto"), ("Pipsy Forex Hub", "forex"), ("Arctic Trade Arena", "other")]  # fmt: skip
HANDLES = ["pay.desk", "fund.now", "topup.hub", "invest.here", "club.fees", "gains.pay"]
WORDS = {
    "en": dict(shares="Shares", qty="Qty", total="Total value", port="Portfolio summary", hold="Holdings",
               stmt="Holding Statement", sec="Security", val="Value", reg="SEBI Registered Broker", regno="Reg. No.",
               pay="Pay to", paybro="Pay your broker", add="Add funds by UPI", lic="Licensed & regulated", upiid="UPI ID", cur="Current value"),
    "hi": dict(shares="शेयर", qty="मात्रा", total="कुल मूल्य", port="पोर्टफोलियो सारांश", hold="होल्डिंग्स",
               stmt="होल्डिंग विवरण", sec="सिक्योरिटी", val="मूल्य", reg="सेबी पंजीकृत ब्रोकर", regno="पंजीकरण संख्या",
               pay="भुगतान करें", paybro="अपने ब्रोकर को भुगतान करें", add="UPI से पैसे जोड़ें", lic="लाइसेंस प्राप्त और विनियमित", upiid="UPI ID",
               cur="वर्तमान मूल्य"),
}  # fmt: skip
CAT_TEXT = {"en": {"crypto": "Crypto exchange", "forex": "Forex trading platform", "other": "Trading platform"},
            "hi": {"crypto": "क्रिप्टो एक्सचेंज", "forex": "फॉरेक्स ट्रेडिंग प्लेटफ़ॉर्म", "other": "ट्रेडिंग प्लेटफ़ॉर्म"}}  # fmt: skip


def inr(n: float) -> str:
    """Indian digit grouping: 1,07,000."""
    s = f"{int(n)}"
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join([*parts, tail])


def short(n: float, hi: bool) -> str:
    """₹ 7.10 L / ₹ 6.22 Cr, the way many apps write a value."""
    lakh, crore = ("लाख", "करोड़") if hi else ("L", "Cr")
    return f"₹ {n / 1e7:.2f} {crore}" if n >= 1e7 else f"₹ {n / 1e5:.2f} {lakh}"


def font(path: str, size: int):
    return ImageFont.truetype(path, size)


def make_case(rng: random.Random, layout: int, lang: str, isins: dict[str, str]) -> dict:
    short_values = rng.random() < 0.5
    n = rng.choice([1, 2, 3, 3, 4]) if layout in (1, 2, 4) else rng.choice([1, 2, 3])
    names = rng.sample(sorted(STOCKS), n)
    holdings = []
    for name in names:
        lo, hi = STOCKS[name]
        qty = rng.choice([25, 40, 100, 150, 250, 500, 750, 1000, 2500, 5000])
        value = round(qty * rng.randint(lo, hi), -2)
        if short_values or layout == 4:  # "₹ 7.10 L" carries only two decimals: keep the label equal to what is printed
            unit = 100_000 if value >= 10_000_000 else 1_000
            value = max(unit, round(value / unit) * unit)
        holdings.append({"name": name, "qty": qty, "value": value, "isin": isins[name]})
    return {
        "layout": layout, "lang": lang, "holdings": holdings if layout in (1, 2, 3, 4) else [],
        "firm": rng.choice(FIRMS), "platform": rng.choice(PLATFORMS), "app": rng.choice(FIRMS),
        "upi": f"{rng.choice(HANDLES)}@{rng.choice(['mockupi', 'validmock'])}",
        "reg_no": f"INZ{rng.randint(0, 10**9 - 1):09d}", "registered": rng.random() < 0.7,
        "short_values": short_values,
    }  # fmt: skip


def status_bar(d, fg="#222222"):
    d.text((50, 30), "9:41", fill=fg, font=font(BOLD, 34))
    d.text((860, 30), "4G  91%", fill=fg, font=font(EN, 30))


def draw(c: dict) -> tuple[Image.Image, list[dict], int | None]:
    """The picture, its labelled claims, and the portfolio total it prints (None if none)."""
    hi, w, lay = c["lang"] == "hi", WORDS[c["lang"]], c["layout"]
    body = HI if hi else EN
    held = c["holdings"]
    total = sum(h["value"] for h in held) if held else None
    img = Image.new("RGB", (W, SCREEN_H), "#ffffff")
    d = ImageDraw.Draw(img)
    claims: list[dict] = []
    shown_total = None
    y = 110

    def hold(h, isin=False, value=False, qty=True):
        return {"type": "holding", "fields": {
            "instrument_name": h["name"], "isin": h["isin"] if isin else None,
            "quantity": h["qty"] if qty else None, "value_inr": h["value"] if value else None}}  # fmt: skip

    if lay == 1:  # cards on a light background
        d.rectangle([0, 0, W, SCREEN_H], fill="#eef2f7")
        status_bar(d)
        d.text((50, y), w["port"], fill="#101828", font=font(BOLD if not hi else HI, 46))
        d.rounded_rectangle([40, y + 90, W - 40, y + 300], 28, fill="#0b5fff")
        d.text((80, y + 120), w["total"], fill="#cfe0ff", font=font(body, 34))
        amt = f"₹ {inr(total)}"
        d.text((80, y + 180), amt, fill="white", font=font(HI, 62))
        shown_total, y = total, y + 340
        for h in held:
            d.rounded_rectangle([40, y, W - 40, y + 190], 22, fill="white", outline="#d0d5dd")
            d.text((80, y + 28), h["name"], fill="#101828", font=font(EN, 38))
            d.text((80, y + 100), f"{w['shares']}: {inr(h['qty'])}", fill="#475467", font=font(body, 32))
            v = short(h["value"], hi) if c["short_values"] else f"₹ {inr(h['value'])}"
            d.text((560, y + 100), v, fill="#101828", font=font(HI, 36))
            claims.append(hold(h, value=True))
            y += 220
    elif lay == 2:  # statement table with ISIN
        status_bar(d)
        d.text((50, y), w["stmt"], fill="#101828", font=font(BOLD if not hi else HI, 46))
        y += 100
        for x, t in ((50, w["sec"]), (430, "ISIN"), (720, w["qty"]), (850, w["val"] + " (₹)")):
            d.text((x, y), t, fill="#667085", font=font(body, 28))
        y += 60
        for h in held:
            d.line([40, y - 10, W - 40, y - 10], fill="#d0d5dd", width=2)
            d.text((50, y + 10), h["name"], fill="#101828", font=font(EN, 23))
            d.text((430, y + 10), h["isin"], fill="#101828", font=font(EN, 26))
            d.text((720, y + 10), inr(h["qty"]), fill="#101828", font=font(EN, 28))
            d.text((850, y + 10), inr(h["value"]), fill="#101828", font=font(EN, 28))
            claims.append(hold(h, isin=True, value=True))
            y += 110
        d.text((50, y + 30), f"{w['total']}   ₹ {inr(total)}", fill="#101828", font=font(HI, 38))
        shown_total, y = total, y + 100
    elif lay == 3:  # tipster chat, quantities only
        d.rectangle([0, 0, W, SCREEN_H], fill="#e8f0e4")
        status_bar(d)
        d.rounded_rectangle([40, y, W - 120, y + 120], 24, fill="white")
        d.text((70, y + 30), c["firm"], fill="#075e54", font=font(BOLD, 36))
        y += 160
        lines = [f"{h['name']}  {w['shares']} {inr(h['qty'])}" for h in held]
        box = 70 + 64 * len(lines) + 150
        d.rounded_rectangle([40, y, W - 80, y + box], 24, fill="white")
        yy = y + 30
        for ln in lines:
            d.text((70, yy), ln, fill="#101828", font=font(body, 34))
            yy += 64
        d.text((70, yy + 20), f"{w['pay']}: {c['upi']}", fill="#101828", font=font(body, 34))
        claims += [hold(h) for h in held]
        claims.append({"type": "payee", "fields": {"upi_id": c["upi"], "account_no_last4": None, "ifsc": None,
                                                    "described_as": "other"}})  # fmt: skip
        y += box
    elif lay == 4:  # statement rows: name, ISIN line, qty and short value
        status_bar(d)
        d.text((50, y), w["hold"], fill="#101828", font=font(BOLD if not hi else HI, 46))
        d.text((50, y + 80), f"{w['total']}  ₹ {inr(total)}", fill="#475467", font=font(HI, 36))
        shown_total, y = total, y + 180
        for h in held:
            d.line([40, y - 12, W - 40, y - 12], fill="#d0d5dd", width=2)
            d.text((50, y), h["name"], fill="#101828", font=font(EN, 38))
            d.text((50, y + 60), f"ISIN: {h['isin']}", fill="#667085", font=font(EN, 28))
            d.text((50, y + 110), f"{w['qty']} {inr(h['qty'])}", fill="#101828", font=font(body, 32))
            d.text((560, y + 110), short(h["value"], hi), fill="#101828", font=font(HI, 34))
            claims.append(hold(h, isin=True, value=True))
            y += 200
    elif lay == 5:  # promo ad naming a firm that says it is registered
        for i in range(SCREEN_H):
            d.line([0, i, W, i], fill=(255, 120 + i // 25, 40 + i // 40))
        status_bar(d, "white")
        d.text(
            (60, y + 60), "40% " + ("रिटर्न की गारंटी" if hi else "guaranteed returns"), fill="white", font=font(HI, 62)
        )
        d.text((60, y + 190), c["firm"], fill="white", font=font(BOLD, 56))
        reg = c["registered"]
        if reg:
            d.text((60, y + 300), w["reg"], fill="white", font=font(body, 38))
            d.text((60, y + 370), f"{w['regno']}: {c['reg_no']}", fill="white", font=font(HI, 34))
        d.text((60, y + 470), f"{w['paybro'] if reg else w['pay']}: {c['upi']}", fill="white", font=font(HI, 38))
        claims += [
            {"type": "broker", "fields": {"name": c["firm"], "sebi_reg_no": c["reg_no"] if reg else None,
                                          "claims_registered": reg}},
            {"type": "payee", "fields": {"upi_id": c["upi"], "account_no_last4": None, "ifsc": None,
                                         "described_as": "broker" if reg else "other"}},
        ]  # fmt: skip
        y += 560
    else:  # platform dashboard
        d.rectangle([0, 0, W, SCREEN_H], fill="#111827")
        status_bar(d, "white")
        pname, cat = c["platform"]
        d.text((60, y + 40), pname, fill="white", font=font(BOLD, 60))
        d.text((60, y + 140), CAT_TEXT[c["lang"]][cat], fill="#9ca3af", font=font(HI, 36))
        d.text((60, y + 230), w["lic"], fill="#34d399", font=font(HI, 38))
        d.text((60, y + 330), w["add"], fill="white", font=font(HI, 36))
        d.text((60, y + 400), f"{w['upiid']}: {c['upi']}", fill="white", font=font(HI, 36))
        claims += [
            {"type": "platform", "fields": {"name": pname, "category": cat, "claims_licensed": True}},
            {"type": "payee", "fields": {"upi_id": c["upi"], "account_no_last4": None, "ifsc": None,
                                         "described_as": "other"}},
        ]  # fmt: skip
        y += 480
    # no on-image banner: any text on the image is read as a claim; labels.json and this script say it is MOCK
    d.rounded_rectangle([W // 2 - 130, SCREEN_H - 40, W // 2 + 130, SCREEN_H - 32], 4, fill="#98a2b3")  # home bar
    return img, claims, shown_total  # the whole phone screen, not just the part with content


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--score-dir", help="only score the images and labels.json already in this folder (no generation)")
    args = ap.parse_args()
    if args.score_dir:
        d = Path(args.score_dir)
        return score(json.loads((d / "labels.json").read_text(encoding="utf-8")), d)
    from app.connectors import isin_master

    isins = {n: isin_master.lookup(n).payload["isin"] for n in STOCKS}
    missing = [n for n, i in isins.items() if not i]
    assert not missing, f"names without exactly one listed ISIN: {missing}"
    rng = random.Random(args.seed)
    OUT.mkdir(parents=True, exist_ok=True)
    labels = {}
    for i in range(60):
        layout, lang = i % 6 + 1, ("en", "hi")[i // 6 % 2]
        case = make_case(rng, layout, lang, isins)
        img, claims, total = draw(case)
        name = f"fa{i + 1:02d}.png"
        img.save(OUT / name)
        labels[name] = {"layout": f"L{layout}", "language": lang, "portfolio_total_inr": total,
                        "claims": [{"id": f"c{k}", **c} for k, c in enumerate(claims, 1)]}  # fmt: skip
    labels = {"_note": "MOCK: fake-app screenshots with made-up firms and handles; not data/frozen", **labels}
    (OUT / "labels.json").write_text(json.dumps(labels, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote 60 screenshots, 6 layouts -> {OUT}")
    if args.score:
        score(labels)


def score(labels: dict, folder: Path = OUT) -> None:
    import os

    os.environ.setdefault("LLM_PROVIDER", "local")
    sys.path.insert(0, str(ROOT / "scripts"))
    from app import main as app_main
    from app.reader import local
    from fastapi.testclient import TestClient
    from run_frozen import by_type, mapped_from_name, same, same_security

    client = TestClient(app_main.app)
    if os.environ["LLM_PROVIDER"] == "local":
        local.warm_up()
    ok = total = 0
    misses = []
    for name, lab in labels.items():
        if name.startswith("_"):
            continue
        r = client.post("/api/read", files={"file": (name, (folder / name).read_bytes(), "image/png")})
        got = by_type(r.json()["claims"]) if r.status_code == 200 else {}
        for key, c in by_type(lab["claims"]).items():
            for f, want in c["fields"].items():
                total += 1
                have = got.get(key, {}).get("fields", {}).get(f, "<not read>")
                mapped = (
                    f == "isin"
                    and want is None
                    and have not in (None, "<not read>")
                    and mapped_from_name(got[key], have)
                )  # the image prints no ISIN; the app fills it in from the name (FR-2.7)
                if same(want, have) or (f == "instrument_name" and same_security(want, have)) or mapped:
                    ok += 1
                else:
                    where = f"{name} ({lab['layout']}, {lab['language']}) {key[0]}#{key[1]} {f}"
                    misses.append(f"{where}: expected {want!r}, got {have!r}")
    print(f"fields right: {ok} / {total}")
    print("\n".join(misses))


if __name__ == "__main__":
    main()
