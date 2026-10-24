"""Local reader number checks, with mocked model output (no GPU): the model's numbers must be backed by the OCR text."""

import json

from app.reader import local
from tests.test_local_reader import SHA


def says(monkeypatch, total, *holdings):
    out = {"language": "en", "portfolio_total_inr": total, "claims": [
        {"type": "holding", "fields": {"instrument_name": n, "isin": None, "quantity": q, "value_inr": v}}
        for n, q, v in holdings]}  # fmt: skip
    monkeypatch.setattr(local, "_ask", lambda *a: json.dumps(out))


def read(raw_ocr):
    cs = local.read_text(local.clean_ocr(raw_ocr), SHA)  # clean_ocr is what local.ocr applies to EasyOCR output
    return cs, [(c.fields.instrument_name, c.fields.quantity, c.fields.value_inr) for c in cs.claims]


def test_hindi_quantity_read_as_rupees_becomes_the_quantity(monkeypatch):
    # EasyOCR gives Devanagari digits; the model put the share count into value_inr
    says(monkeypatch, None, ("Acme Textiles", None, 770))
    cs, got = read("Acme Textiles\nशेयर: ७७०")
    print(f"\n{got}, language {cs.language}")
    assert got == [("Acme Textiles", 770, None)] and cs.language == "hi"


def test_total_copied_into_a_single_holding_is_dropped(monkeypatch):
    says(monkeypatch, 4410000, ("Acme Textiles", 1470, 4410000))
    cs, got = read("Acme Textiles\nमात्राः १,४७०\nकुल पोर्टफोलियोः र ४४,१०,०००")  # ₹ read as र
    print(f"\n{got}, total {cs.portfolio_total_inr}")
    assert got == [("Acme Textiles", 1470, None)] and cs.portfolio_total_inr == 4410000


def test_a_line_labelled_as_the_holdings_value_keeps_it(monkeypatch):
    says(monkeypatch, 3360000, ("Acme Textiles", 1200, 3360000))
    cs, got = read("Acme Textiles\nShares held: 1,200\nValue of this holding: Rs. 33,60,000\nTotal: Rs. 33,60,000")
    assert got == [("Acme Textiles", 1200, 3360000)] and cs.portfolio_total_inr == 3360000


def test_total_line_read_as_a_holding_becomes_the_total(monkeypatch):
    says(monkeypatch, None, ("Acme Textiles", 90, 270000), ("Total value", None, 270000))
    cs, got = read("Acme Textiles 90 Shares Rs. 2,70,000\nTotal value Rs. 2,70,000")
    assert got == [("Acme Textiles", 90, 270000)] and cs.portfolio_total_inr == 270000


def test_numbers_the_text_does_not_show_are_null(monkeypatch):
    says(monkeypatch, 216000, ("Acme Textiles", 80, 216000))  # a tenth of the printed total, invented
    cs, got = read("Total portfolio value Rs. २1,60,0००\nAcme Textiles\nQty ८०")
    print(f"\n{got}, total {cs.portfolio_total_inr}")
    assert got == [("Acme Textiles", 80, None)] and cs.portfolio_total_inr is None


def test_crore_and_lakh_amounts_count_as_printed(monkeypatch):
    says(monkeypatch, 39800000, ("Acme Textiles", 100, None))
    cs, _ = read("Acme Textiles 100 shares\nPortfolio ₹3.98 crore")
    assert cs.portfolio_total_inr == 39800000
