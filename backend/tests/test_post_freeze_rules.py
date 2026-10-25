"""Rule changes made after the first frozen-set run (see progress.md, "post-freeze change"). Names come from the public
lists at run time or are made up here; nothing is copied from data/frozen."""

import csv
import json

import pytest

from app.connectors import isin_master, sebi
from app.connectors.names import normalize, normalize_security
from app.reader import local
from app.schemas.claims import HoldingClaim
from app.verdict import rules
from tests.helpers import ROOT
from tests.test_rules import INFY, OTHER, RELIANCE, aa, broker, check

SHA_ZERO = "0" * 64


def holding(name, isin, qty=10):
    return HoldingClaim(
        id="c1", type="holding", fields={"instrument_name": name, "isin": isin, "quantity": qty, "value_inr": None}
    )


def mapped(name, isin=None):
    return isin_master.lookup(name, isin)


def an_extended_name():
    """A listed name that other, longer listed names start with, found in the lists rather than written down."""
    index = isin_master._index()
    for key, found in index.items():
        longer = {i for k, f in index.items() if k.startswith(key + " ") for i, _ in f}
        if key and longer and not longer <= {i for i, _ in found}:
            return key
    pytest.skip("no listed name is a prefix of another")


# a bare name that longer listed names extend is ambiguous: the customer may hold any of them
def test_name_that_longer_listed_names_extend_is_ambiguous():
    name = an_extended_name()
    rec = mapped(name)
    assert rec.payload["isin"] is None and rec.payload["candidates"] > 1
    check(rules.holding(holding(name, None), aa(cdsl=[(OTHER, 1)]), rec), "NO_RECORD", "HOLDING_NAME_AMBIGUOUS")
    assert len(isin_master.candidates(name)) == rec.payload["candidates"]


def test_a_name_nothing_extends_still_maps_to_its_one_isin():
    rec = mapped("Infosys")
    assert rec.payload["isin"] == INFY and rec.payload["candidates"] == 1 and rec.payload["listed"]


# an ISIN on neither list is likelier a misread than a security
def test_unlisted_isin_is_unmapped_not_contradicted_even_when_every_depository_answered():
    unlisted = "INE000ZZ0000"
    assert unlisted not in isin_master.listed_isins() and mapped("X", unlisted).payload["listed"] is False
    check(
        rules.holding(holding("X", unlisted), aa(cdsl=[(OTHER, 1)]), mapped("X", unlisted)),
        "NO_RECORD",
        "HOLDING_ISIN_UNMAPPED",
    )
    check(
        rules.holding(holding("X", unlisted), aa(cdsl=[(OTHER, 1)], failed=["NSDL"]), mapped("X", unlisted)),
        "NO_RECORD",
        "HOLDING_ISIN_UNMAPPED",
    )  # identity is settled before coverage


def test_listed_isin_not_held_still_contradicts_and_a_held_unlisted_isin_still_matches():
    check(
        rules.holding(holding("Reliance", RELIANCE), aa(cdsl=[(OTHER, 1)]), mapped("Reliance", RELIANCE)),
        "CONTRADICTS",
        "HOLDING_NOT_FOUND_ALL_DEPOSITORIES",
    )
    unlisted = "INE000ZZ0000"
    check(
        rules.holding(holding("X", unlisted, 5), aa(cdsl=[(unlisted, 5)]), mapped("X", unlisted)),
        "MATCHES",
        "HOLDING_FOUND",
    )


# a broker name one typo from a registered firm is never CONTRADICTS, wherever the typo is
def a_registered_securities_firm():
    """The first registered broker whose name ends in "SECURITIES LIMITED", taken from the list."""
    with (ROOT / "data" / "registries" / "sebi_brokers.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["Name"]
            if name.isascii() and name.upper().endswith(" SECURITIES LIMITED") and 22 <= len(name) <= 32:
                return name
    pytest.skip("no suitable registered broker")


@pytest.mark.parametrize("where", ["drop", "double", "swap"])
def test_one_typo_anywhere_in_a_registered_name_is_a_near_match(where):
    name = a_registered_securities_firm()
    word = "SECURITIES"
    typo = {
        "drop": word.replace("CUR", "CR"),
        "double": word.replace("TIES", "TIIES"),
        "swap": word.replace("SE", "ES"),
    }
    typed = name.upper().replace(word, typo[where])
    assert normalize(name) != normalize(typed) and sebi.lookup(name, None).payload["exact"]
    check(broker(typed), "NO_RECORD", "BROKER_NEAR_MATCH")


def test_two_typos_or_a_different_firm_is_not_a_near_match():
    check(broker("Kotak Securtes Limted"), "CONTRADICTS", "BROKER_NOT_ON_SEBI_LIST")
    check(broker("Quillfeather Wealth Desk"), "CONTRADICTS", "BROKER_NOT_ON_SEBI_LIST")


def test_a_hindi_name_is_kept_not_erased_and_never_near_matches_by_accident():
    name = "नीलकमल स्टॉक सेवा"
    assert normalize(name) and normalize_security(name)
    assert sebi.lookup(name, None).payload["near"] is None
    check(broker(name), "CONTRADICTS", "BROKER_NOT_ON_SEBI_LIST")


def test_a_registration_number_nobody_holds_falls_back_to_the_name_logic():
    check(broker("Quillfeather Wealth Desk", "INZ000000001"), "CONTRADICTS", "BROKER_NOT_ON_SEBI_LIST")
    check(
        broker("Quillfeather Wealth Desk", "INZ000000001", claims_registered=False),
        "NO_RECORD",
        "BROKER_NOT_FOUND_NOT_CLAIMED",
    )


# OCR repairs: an ISIN misread with look-alike glyphs, and identifiers whose printed format fixes the reading
def test_isin_misread_with_lookalike_glyphs_is_repaired_only_to_a_listed_isin():
    assert isin_master.repair_isin("INEO02A01018") == RELIANCE  # O for 0
    assert isin_master.repair_isin("INEOO2A01018") == RELIANCE  # two swaps
    assert isin_master.repair_isin(RELIANCE) == RELIANCE and isin_master.repair_isin(None) is None
    unlisted = "INE000ZZ0000"
    assert isin_master.repair_isin(unlisted) == unlisted  # nothing listed is one swap away: left as read
    assert isin_master.repair_isin("INE0O2A01019") == "INE0O2A01019"  # fails the check digit: never guessed


def test_check_digit_accepts_real_isins_and_rejects_a_changed_digit():
    assert isin_master._check_digit_ok(RELIANCE) and isin_master._check_digit_ok(INFY)
    assert not isin_master._check_digit_ok("INE002A01019")


def test_ocr_cleanup_repairs_registration_numbers_handles_and_a_zero_inside_a_word():
    from app.reader.local import clean_ocr

    assert "INZ000031633" in clean_ocr("SEBI Reg. No.: |NZ000031633")
    assert "INZ000O31633".replace("O", "0") in clean_ocr("Reg No INZO00031633")  # letter O inside the digits
    assert "ravi.brk@validbank" in clean_ocr("ravi . brkavalidbank")
    assert "Zer0dha Broking" in clean_ocr("ZerOdha Broking")
    assert (
        clean_ocr("Get 5OO fund") == "Get 5OO fund" and clean_ocr("OPEN NOW") == "OPEN NOW"
    )  # not in a lower-case word


# model output clean-up (reader/local.py)
def holding_claim(name, value):
    return {"type": "holding", "fields": {"instrument_name": name, "isin": None, "quantity": 1, "value_inr": value}}


def test_words_for_null_and_page_headings_are_not_claims():
    from app.reader.local import _tidy

    claims = [
        {"type": "broker", "fields": {"name": "null", "sebi_reg_no": None, "claims_registered": False}},
        {"type": "broker", "fields": {"name": "Holdings", "sebi_reg_no": "null", "claims_registered": False}},
        {"type": "broker", "fields": {"name": "होल्डिंग्स", "sebi_reg_no": None, "claims_registered": False}},
        {
            "type": "broker",
            "fields": {"name": "Quillfeather Wealth Desk", "sebi_reg_no": "None", "claims_registered": True},
        },
        {"type": "payee", "fields": {"upi_id": "N/A", "account_no_last4": None, "ifsc": None, "described_as": "other"}},
    ]
    kept = _tidy(claims)
    assert [c["fields"].get("name") for c in kept if c["type"] == "broker"] == ["Quillfeather Wealth Desk"]
    assert kept[0]["fields"]["sebi_reg_no"] is None and kept[1]["fields"]["upi_id"] is None


def test_a_stray_leading_2_from_a_misread_rupee_sign_is_removed_only_when_the_total_proves_it():
    from app.reader.local import _repair_rupee_digit

    lines = [holding_claim("A", 852500.0), holding_claim("B", 62250000.0), holding_claim("C", 260800.0)]
    _repair_rupee_digit(lines, 63163300)
    assert [c["fields"]["value_inr"] for c in lines] == [852500.0, 62250000.0, 60800.0]
    unproven = [holding_claim("A", 852500.0), holding_claim("C", 260800.0)]
    _repair_rupee_digit(unproven, 99999999)  # the total does not fit any single fix: left alone
    assert unproven[1]["fields"]["value_inr"] == 260800.0
    ok = [holding_claim("A", 200.0), holding_claim("B", 300.0)]
    _repair_rupee_digit(ok, 500)  # already adds up: a real 2xx value is never touched
    assert ok[0]["fields"]["value_inr"] == 200.0


def test_the_model_layout_becomes_a_claims_list():
    from app.reader.local import _as_claims, model_schema

    assert set(model_schema()["properties"]) == {
        "language",
        "portfolio_total_inr",
        "holdings",
        "broker",
        "payee",
        "platform",
    }
    claims = _as_claims(
        {"holdings": [{"instrument_name": "A"}], "broker": {"name": "B"}, "payee": None, "platform": None}
    )
    assert [c["type"] for c in claims] == ["holding", "broker"]


def test_a_firm_is_registered_only_if_the_text_says_so_and_an_isin_stays_on_one_holding():
    from app.reader.local import _ground

    broker_claim = {"type": "broker", "fields": {"name": "X Desk", "sebi_reg_no": None, "claims_registered": True}}
    _ground([broker_claim], "X Desk\nmargin to your broker")
    assert broker_claim["fields"]["claims_registered"] is False
    broker_claim["fields"]["claims_registered"] = True
    _ground([broker_claim], "X Desk\nSEBI Registered Broker")
    assert broker_claim["fields"]["claims_registered"] is True
    text = "Alpha Mills\n12,000\nBeta Works\n9,000\nISIN: INE000AA0001\nQty 5"
    a = {"type": "holding", "fields": {"instrument_name": "Alpha Mills", "isin": "INE000AA0001"}}
    b = {"type": "holding", "fields": {"instrument_name": "Beta Works", "isin": "INE000AA0001"}}
    _ground([a, b], text)
    assert a["fields"]["isin"] is None and b["fields"]["isin"] == "INE000AA0001"  # the ISIN follows Beta Works


def test_a_single_holding_keeps_its_value_even_when_it_equals_the_total():
    from app.reader.local import _check_numbers

    holding = {"type": "holding", "fields": {"instrument_name": "Alpha Mills", "quantity": 5, "value_inr": 5975000.0}}
    claims, total = _check_numbers([holding], 5975000.0, "Alpha Mills\nQuantity 5\nCurrent value ₹ 59,75,000")
    assert claims[0]["fields"]["value_inr"] == 5975000.0


def test_second_reading_adds_a_handle_the_first_reading_lost():
    from app.reader import local, offline

    if not offline.os.path.exists(offline.TESSERACT):
        pytest.skip("Tesseract not installed")
    image = (ROOT / "data" / "demo_cache" / "demo-001.png").read_bytes()
    assert local.second_reading(image, "no handle here").count("UPI ID: ") == 1
    text = local.ocr(image)
    assert text.count("zyphrastock.invest@mockupi") <= 2  # already read by the first engine: not added twice


def test_a_printed_upi_handle_becomes_a_payee_when_the_model_returned_none():
    from app.reader.local import _payee_from_text

    text = "Quillfeather Desk\nSEBI Registered Broker\nUPI ID:\nquill . deskemockupi\nUPI ID: quill.desk@mockupi"
    claims = [
        {"type": "payee", "fields": {"upi_id": None, "account_no_last4": None, "ifsc": None, "described_as": "other"}}
    ]
    _payee_from_text(claims, text)
    assert [(c["fields"]["upi_id"], c["fields"]["described_as"]) for c in claims] == [("quill.desk@mockupi", "broker")]
    advisor = []
    _payee_from_text(advisor, "सलाहकार\nUPI: a.b@mockupi")
    assert advisor[0]["fields"]["described_as"] == "advisor"
    none = []
    _payee_from_text(none, "no handle in this text")
    assert none == []


def test_indian_amount_units_l_and_cr_are_read():
    from app.reader.local import _amounts

    got = _amounts("₹ 2.76 L ₹ 1.70 Cr ₹ 37.20 लाख ₹ 3.98 crore ₹ 4,500")
    assert got == pytest.approx([276000, 17000000, 3720000, 39800000, 4500])


def test_missing_holding_is_asked_for_once_when_the_lines_do_not_add_up_to_the_printed_total(monkeypatch):
    from app.reader import local

    text = "कुल\n₹ 10,00,000\nAlpha Mills\n₹ 4,00,000\nShares: 4\nBeta Works\n₹ 6,00,000\nShares: 6"
    alpha = '{"instrument_name":"Alpha Mills","isin":null,"quantity":4,"value_inr":400000}'
    beta = '{"instrument_name":"Beta Works","isin":null,"quantity":6,"value_inr":600000}'
    tail = '"broker":null,"payee":null,"platform":null}'
    first = f'{{"language":"hi","portfolio_total_inr":1000000,"holdings":[{alpha}],{tail}'
    second = f'{{"language":"hi","portfolio_total_inr":1000000,"holdings":[{alpha},{beta}],{tail}'
    notes = []

    def ask(model, t, note, deadline):
        notes.append(note)
        return second if note else first

    monkeypatch.setattr(local, "_ask", ask)
    cs = local.read_text(text, SHA_ZERO)
    assert [c.fields.instrument_name for c in cs.claims] == [
        "Alpha Mills",
        "Beta Works",
    ] and cs.portfolio_total_inr == 1000000
    assert notes[0] is None and "add up to 400000 but the page total is 1000000" in notes[1] and len(notes) == 2
    monkeypatch.setattr(local, "_ask", lambda *a: first)  # the retry changes nothing: the first answer stands
    assert len(local.read_text(text, SHA_ZERO).claims) == 1


def test_a_rupee_amount_written_with_a_unit_fills_a_value_the_model_left_null():
    from app.reader.local import _fill_values

    text = (
        "Total value\n₹ 3,00,000\nAlpha Mills\n₹ 1.50 L\nShares: 10\nBeta Works\n₹ 0.30 L\nShares: 5\n"
        "Gamma Ltd\nShares: 2"
    )
    claims = [
        {"type": "holding", "fields": {"instrument_name": n, "isin": None, "quantity": q, "value_inr": v}}
        for n, q, v in (("Alpha Mills", 10, None), ("Beta Works", 5, 30000.0), ("Gamma Ltd", 2, None))
    ]
    _fill_values(claims, text)
    assert [c["fields"]["value_inr"] for c in claims] == [150000.0, 30000.0, None]  # Gamma prints no amount: stays null


def test_a_value_the_model_got_wrong_is_read_off_the_page():
    text = "Total value\n₹ 80,000\nAlpha Mills\n₹ 7.10 L\nShares: 10\nBeta Works\n₹ 0.90 L\nShares: 5"
    model = {
        "language": "en",
        "portfolio_total_inr": 80000,
        "holdings": [
            {"instrument_name": "Alpha Mills", "isin": None, "quantity": 10, "value_inr": 7100000},  # 10x too large
            {"instrument_name": "Beta Works", "isin": None, "quantity": 5, "value_inr": 90000},
        ],
        "broker": None,
        "payee": None,
        "platform": None,
    }
    cs = local._to_claimset(json.dumps(model), SHA_ZERO, "m", text)
    assert [c.fields.value_inr for c in cs.claims] == [710000, 90000]


def test_a_garbled_isin_is_replaced_by_the_listed_one_the_page_prints_but_a_printed_one_stays():
    text = f"Infosys Ltd\nISIN: {INFY.replace('0', 'O', 2)}\nQty 40"  # printed with O for 0
    held = [{"type": "holding", "fields": {"instrument_name": "Infosys Ltd", "isin": INFY[:-1], "quantity": 40}}]
    local._isins_from_text(held, text)
    assert held[0]["fields"]["isin"] == INFY  # one character dropped by the model
    fake = "INE000Z01010"
    held = [{"type": "holding", "fields": {"instrument_name": "X", "isin": fake, "quantity": 1}}]
    local._isins_from_text(held, f"X\nISIN {fake}\n{INFY}")
    assert held[0]["fields"]["isin"] == fake  # printed as such: never swapped for another


def test_a_payee_is_described_as_broker_or_advisor_only_if_the_text_uses_the_word():
    def payee(said):
        return [{"type": "payee", "fields": {"upi_id": "a@b", "described_as": said}}]

    for said, text, want in (
        ("broker", "Add funds by UPI", "other"),
        ("broker", "सलाहकार को भुगतान करें", "advisor"),
        ("broker", "Pay your broker", "broker"),
        ("advisor", "Add funds", "other"),
    ):
        c = payee(said)
        local._ground_payee(c, text)
        assert c[0]["fields"]["described_as"] == want


def test_ocr_cleanup_lost_points_ltd_and_grouped_quantities():
    assert local.clean_ocr("Infosys Lta") == "Infosys Ltd"
    assert "₹ 7.68 लाख" in local.clean_ocr("₹ 7 68 लाख")
    assert "₹ 6.84 लाख" in local.clean_ocr("₹ 684 लाख")
    assert "1.14 लाख" in local.clean_ocr("1.14 लाख")  # already has its point
    assert "₹ 1,50,000" in local.clean_ocr("₹ 1,50,000")
    assert "मातरा 2,500" in local.clean_ocr("मातरा 2 500")
    assert "Qty 250" in local.clean_ocr("Qty 250")


def test_a_decimal_amount_with_a_unit_but_no_rupee_sign_fills_a_value():
    claims = [
        {"type": "holding", "fields": {"instrument_name": n, "isin": None, "quantity": 1, "value_inr": None}}
        for n in ("Alpha Mills", "Beta Works")
    ]
    local._fill_values(claims, "Alpha Mills\nQty 2,500\n89.60 L\nBeta Works\nQty 40\n₹ 1.43 L")
    assert [c["fields"]["value_inr"] for c in claims] == [8960000, 143000]


def test_a_total_after_a_stray_rupee_sign_is_still_the_total():
    assert local._printed_total("Total value\nरे\n6,76,000\nAlpha Mills") == 676000


def test_a_short_handle_is_completed_from_the_printed_one_and_a_reg_no_is_taken_from_the_page():
    text = "UPI ID:\ntopup hub@validmock\nUPI ID: topup.hub@validmock\nSEBI Reg. No.: INZ778246640"
    claims = [
        {"type": "payee", "fields": {"upi_id": "hub@validmock"}},
        {"type": "broker", "fields": {"name": "Kiran Wealth Circle", "sebi_reg_no": None}},
    ]
    local._complete_handle(claims, text)
    local._reg_no_from_text(claims, text)
    assert claims[0]["fields"]["upi_id"] == "topup.hub@validmock"
    assert claims[1]["fields"]["sebi_reg_no"] == "INZ778246640"
    local._reg_no_from_text(claims, "INZ000000001 and INZ000000002")  # two different numbers: ambiguous, left alone
    claims[1]["fields"]["sebi_reg_no"] = None
    local._reg_no_from_text(claims, "INZ000000001 and INZ000000002")
    assert claims[1]["fields"]["sebi_reg_no"] is None


def test_platform_category_needs_a_cue_and_the_name_is_not_the_category_line_or_a_handle_part():
    text = "9:41\n4G 91%\nKubera Coin\nExchange\nक्रिप्टो एक्सचेंज\nUPI ID: fxfunds.in@mockupi"
    claims = [{"type": "platform", "fields": {"name": "fxfunds . in", "category": "crypto", "claims_licensed": True}}]
    local._ground_platform(claims, text)
    assert claims[0]["fields"]["name"] == "Kubera Coin Exchange" and claims[0]["fields"]["category"] == "crypto"
    plain = [{"type": "platform", "fields": {"name": "Arena", "category": "forex", "claims_licensed": True}}]
    local._ground_platform(plain, "Arena\nTrading platform")
    assert plain[0]["fields"]["category"] == "other"  # the text never says forex


def test_more_ocr_habits_from_realistic_screenshots():
    assert "₹ 7.10 L" in local.clean_ocr("₹ 7110 L")  # the point read as 1
    assert "INZ000917334" in local.clean_ocr("पंजीकरण संख्याः INZ00091 7334")  # a gap inside a registration number
    assert "INZ000917334 x" in local.clean_ocr("INZ000917334 x")
    assert "शेयर 150" in local.clean_ocr("शेयर 1 50")
    assert "शेयर 2,000" in local.clean_ocr("शेयर 2,000")
    assert isin_master.repair_isin("INE397001024") == "INE397D01024"  # D read as 0


def test_a_holding_worth_more_than_the_whole_portfolio_is_a_misread():
    text = "Total value\n₹ 36,04,000\nAsian Paints Ltd\n₹ 7110 L"
    claims = [
        {"type": "holding", "fields": {"instrument_name": "Asian Paints Ltd", "quantity": 250, "value_inr": 711e6}}
    ]
    claims, total = local._check_numbers(claims, 3604000, local.clean_ocr(text))
    assert total == 3604000 and claims[0]["fields"]["value_inr"] is None


def test_handle_with_a_space_for_its_dot_is_completed_but_label_words_are_not_joined():
    text = "your broker: quantrix pay@mockupi"
    claims = [{"type": "payee", "fields": {"upi_id": "pay@mockupi"}}]
    local._complete_handle(claims, text)
    assert claims[0]["fields"]["upi_id"] == "quantrix.pay@mockupi"
    claims = [{"type": "payee", "fields": {"upi_id": "pay@mockupi"}}]
    local._complete_handle(claims, "Pay to pay@mockupi")
    assert claims[0]["fields"]["upi_id"] == "pay@mockupi"
