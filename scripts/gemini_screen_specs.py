# ruff: noqa: E501  (the CASES table keeps one prompt per few lines)
"""Specs for the realistic fake-app screenshots made with an image generator (the "unseen style" test set).

Usage: python -X utf8 scripts/gemini_screen_specs.py [--prompts]     print every prompt to paste into the generator
       python -X utf8 scripts/gemini_screen_specs.py --labels DIR    write DIR/labels.json from the specs
Each image is generated from the exact text of its prompt; the label says what the image should show. After
generating, look at every image and edit the spec if the generator changed a word or number: a label must say
what the image shows. MOCK data: invented apps, firms and handles; listed company names are public securities.
These images are AI-generated; list them in the deck's disclosure slide. Not data/frozen.
"""

import json
import sys
from pathlib import Path

ISIN = {
    "Reliance Industries Ltd": "INE002A01018", "Infosys Ltd": "INE009A01021", "HDFC Bank Ltd": "INE040A01034",
    "Tata Consultancy Services Ltd": "INE467B01029", "ICICI Bank Ltd": "INE090A01021",
    "Bharti Airtel Ltd": "INE397D01024", "Larsen & Toubro Ltd": "INE018A01030",
    "Asian Paints Ltd": "INE021A01026", "State Bank of India": "INE062A01020", "Titan Company Ltd": "INE280A01028",
}  # fmt: skip
STYLE = (
    "a realistic full-screen portrait Android phone screenshot (tall 9:19.5, no phone frame, nothing cropped) of a "
    "made-up app. Status bar at the top: 9:41 on the left, 4G and 91% battery on the right. Spell every word and "
    "number exactly as written, sharp and legible. No other text."
)
H, B, P, PL = "holding", "broker", "payee", "platform"


def hold(name, qty, value=None, isin=False):
    return {"type": H, "fields": {"instrument_name": name, "isin": ISIN[name] if isin else None,
                                  "quantity": qty, "value_inr": value}}  # fmt: skip


def payee(upi, as_="other"):
    return {"type": P, "fields": {"upi_id": upi, "account_no_last4": None, "ifsc": None, "described_as": as_}}


def broker(name, reg=None, registered=True):
    return {"type": B, "fields": {"name": name, "sebi_reg_no": reg, "claims_registered": registered}}


def platform(name, cat):
    return {"type": PL, "fields": {"name": name, "category": cat, "claims_licensed": True}}


# name -> (layout, language, total, prompt body, claims)
CASES = {
    "gm01": ("cards", "en", 2770000,
             "The app is called Meridian Trade. Page title: Portfolio summary. A blue card with the label Total value and "
             "the amount ₹ 27,70,000. Below it three white holding cards, each with the share name, a Shares line and the "
             "value: 1) Reliance Industries Ltd, Shares: 500, ₹ 7,05,000. 2) Infosys Ltd, Shares: 250, ₹ 4,25,000. "
             "3) HDFC Bank Ltd, Shares: 1,000, ₹ 16,40,000. Icons only in the bottom bar.",
             [hold("Reliance Industries Ltd", 500, 705000), hold("Infosys Ltd", 250, 425000),
              hold("HDFC Bank Ltd", 1000, 1640000)]),
    "gm02": ("table", "en", 3290000,
             "The app is called Orbit Gains. Page title: Holding Statement. A table with the column headings Security, "
             "ISIN, Qty, Value (₹), and two rows. Row 1: Tata Consultancy Services Ltd, INE467B01029, 400, 14,80,000. "
             "Row 2: ICICI Bank Ltd, INE090A01021, 1,500, 18,10,000. Under the table a line: Total value ₹ 32,90,000.",
             [hold("Tata Consultancy Services Ltd", 400, 1480000, True), hold("ICICI Bank Ltd", 1500, 1810000, True)]),
    "gm03": ("chat", "en", None,
             "A WhatsApp-style chat, light green background, contact name at the top: Falcon Alpha Traders. One white "
             "message bubble with these lines: Bharti Airtel Ltd Shares 1,200 / Larsen & Toubro Ltd Shares 300 / "
             "Pay to: club.fees@mockupi",
             [hold("Bharti Airtel Ltd", 1200), hold("Larsen & Toubro Ltd", 300), payee("club.fees@mockupi")]),
    "gm04": ("rows", "en", 3604000,
             "The app is called Kiran Wealth. Page title: Holdings. Under it: Total value ₹ 36,04,000. Then a list with "
             "two entries, each with the share name, then a smaller line with its ISIN, then a line with the quantity "
             "and the value. Entry 1: Asian Paints Ltd, ISIN: INE021A01026, Qty 250, ₹ 7.10 L. Entry 2: State Bank of "
             "India, ISIN: INE062A01020, Qty 3,000, ₹ 28.94 L.",
             [hold("Asian Paints Ltd", 250, 710000, True), hold("State Bank of India", 3000, 2894000, True)]),
    "gm05": ("promo", "en", None,
             "An orange advertisement screen. Big text: 40% guaranteed returns. Below it the firm name Quantrix Growth "
             "Hub. Below that: SEBI Registered Broker and Reg. No.: INZ000482917. At the bottom: Pay your broker: "
             "quantrix.pay@mockupi",
             [broker("Quantrix Growth Hub", "INZ000482917"), payee("quantrix.pay@mockupi", "broker")]),
    "gm06": ("platform", "en", None,
             "A dark navy trading platform home screen. App name: Zenfx Markets. Under it: Forex trading platform. A "
             "green line: Licensed & regulated. Then the lines: Add funds by UPI and UPI ID: topup.hub@validmock",
             [platform("Zenfx Markets", "forex"), payee("topup.hub@validmock")]),
    "gm07": ("cards", "hi", 3150000,
             "The app is called Vertex Trade. Page title in Hindi: पोर्टफोलियो सारांश. A blue card with the Hindi label "
             "कुल मूल्य and the amount ₹ 31,50,000. Below it two white holding cards, each with the share name, a Hindi "
             "शेयर line and the value: 1) Titan Company Ltd, शेयर: 600, ₹ 21,00,000. 2) Infosys Ltd, शेयर: 750, "
             "₹ 10,50,000.",
             [hold("Titan Company Ltd", 600, 2100000), hold("Infosys Ltd", 750, 1050000)]),
    "gm08": ("rows", "hi", 4120000,
             "The app is called Meridian Trade. Page title in Hindi: होल्डिंग्स. Under it, in Hindi: कुल मूल्य ₹ "
             "41,20,000. Then a list with two entries, each with the share name, a smaller line with its ISIN, and a "
             "line with the Hindi word मात्रा and the quantity and the value. Entry 1: Reliance Industries Ltd, ISIN: "
             "INE002A01018, मात्रा 1,000, 28.50 लाख. Entry 2: HDFC Bank Ltd, ISIN: INE040A01034, मात्रा 700, 12.70 लाख.",
             [hold("Reliance Industries Ltd", 1000, 2850000, True), hold("HDFC Bank Ltd", 700, 1270000, True)]),
    "gm09": ("promo", "hi", None,
             "An orange advertisement screen in Hindi. Big text: 40% रिटर्न की गारंटी. Below it the firm name Sunrise "
             "Profit Club. Below that in Hindi: सेबी पंजीकृत ब्रोकर and पंजीकरण संख्या: INZ000917334. At the bottom in "
             "Hindi: भुगतान करें: sunrise.fees@mockupi",
             [broker("Sunrise Profit Club", "INZ000917334"), payee("sunrise.fees@mockupi", "broker")]),
    "gm10": ("platform", "hi", None,
             "A dark navy exchange home screen. App name: Bitora Exchange. Under it in Hindi: क्रिप्टो एक्सचेंज. A green "
             "line in Hindi: लाइसेंस प्राप्त और विनियमित. Then in Hindi: UPI से पैसे जोड़ें and the line UPI ID: "
             "gains.pay@mockupi",
             [platform("Bitora Exchange", "crypto"), payee("gains.pay@mockupi")]),
    "gm11": ("table", "hi", 5260000,
             "The app is called Falcon Alpha. Page title in Hindi: होल्डिंग विवरण. A table with the headings सिक्योरिटी, "
             "ISIN, मात्रा, मूल्य (₹) and two rows. Row 1: Larsen & Toubro Ltd, INE018A01030, 800, 28,40,000. Row 2: "
             "Bharti Airtel Ltd, INE397D01024, 1,400, 24,20,000. Under the table in Hindi: कुल मूल्य ₹ 52,60,000.",
             [hold("Larsen & Toubro Ltd", 800, 2840000, True), hold("Bharti Airtel Ltd", 1400, 2420000, True)]),
    "gm12": ("chat", "hi", None,
             "A WhatsApp-style chat in Hindi, light green background, contact name at the top: Silverline Capital Circle. "
             "One white message bubble with these lines: State Bank of India शेयर 2,000 / Asian Paints Ltd शेयर 150 / "
             "भुगतान करें: fund.now@mockupi",
             [hold("State Bank of India", 2000), hold("Asian Paints Ltd", 150), payee("fund.now@mockupi")]),
}  # fmt: skip


def prompt(name: str) -> str:
    return f"Generate an image: {STYLE.replace('of a made-up app.', 'of a made-up app. ' + CASES[name][3])}"


def labels() -> dict:
    out = {"_note": "MOCK: images made with an image generator from scripts/gemini_screen_specs.py; not data/frozen"}
    for n, (layout, lang, total, _, claims) in CASES.items():
        out[f"{n}.png"] = {"layout": layout, "language": lang, "portfolio_total_inr": total,
                           "claims": [{"id": f"c{i}", **c} for i, c in enumerate(claims, 1)]}  # fmt: skip
    return out


if __name__ == "__main__":
    if "--labels" in sys.argv:
        d = Path(sys.argv[sys.argv.index("--labels") + 1])
        d.mkdir(parents=True, exist_ok=True)
        (d / "labels.json").write_text(json.dumps(labels(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {d / 'labels.json'}")
    else:
        for n in CASES:
            print(f"--- {n}\n{prompt(n)}\n")
