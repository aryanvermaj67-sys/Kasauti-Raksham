"""Rule changes made after the first frozen-set run (see progress.md, "post-freeze change"). Names come from the public
lists at run time or are made up here; nothing is copied from data/frozen."""

import pytest

from app.connectors import isin_master, sebi
from app.connectors.names import normalize, normalize_security
from app.schemas.claims import HoldingClaim
from app.verdict import rules
from tests.test_rules import INFY, OTHER, RELIANCE, aa, broker, check


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
@pytest.mark.parametrize("typo", ["Kotak Securties Limited", "Kotak Securitiess Limited", "Kotk Securities Limited"])
def test_one_typo_anywhere_in_a_registered_name_is_a_near_match(typo):
    assert normalize("Kotak Securities Limited") != normalize(typo)
    check(broker(typo), "NO_RECORD", "BROKER_NEAR_MATCH")


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
