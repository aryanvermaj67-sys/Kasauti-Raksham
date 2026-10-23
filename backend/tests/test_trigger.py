"""FR-1.2 trigger: the rule, one prompt per campaign, and inputs that never include age, gender, language or region."""

import pytest

from app import trigger
from app.connectors import suspect_registry


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(trigger, "ACKS", tmp_path / "acks.json")
    monkeypatch.setattr(suspect_registry, "ADDITIONS", tmp_path / "additions.json")


def t(n, day, payee, amount, narration="payment", new=True):
    return {
        "txn_id": f"T{n}",
        "date": f"2026-08-{day:02d}",
        "payee": payee,
        "amount_inr": amount,
        "narration": narration,
        "new_payee": new,
    }


class Recording(dict):
    """A transaction that remembers which fields the rule read."""

    read: set = set()

    def __getitem__(self, key):
        Recording.read.add(key)
        return super().__getitem__(key)


def test_rule_reads_only_transaction_fields_never_personal_attributes():
    rows = [r for r in trigger.ledger() if r["customer_id"] in {"SYN-C0001", "SYN-C0011"}]
    assert not {"age", "gender", "language", "region", "state", "city"} & {k for r in trigger.ledger() for k in r}
    trigger.evaluate([Recording({k: r[k] for k in trigger.FIELDS}) for r in rows])
    assert Recording.read <= set(trigger.FIELDS)


def test_rising_transfers_to_new_payees_in_14_days():
    burst = [t(1, 1, "a@mockupi", 5000), t(2, 4, "b@mockupi", 9000), t(3, 9, "c@mockupi", 20000)]
    assert [p["reason"] for p in trigger.evaluate(burst)] == ["rising_transfers_to_new_payees"]
    falling = [t(1, 1, "a@mockupi", 20000), t(2, 4, "b@mockupi", 9000), t(3, 9, "c@mockupi", 5000)]
    spread = [t(1, 1, "a@mockupi", 5000), t(2, 12, "b@mockupi", 9000), t(3, 28, "c@mockupi", 20000)]
    assert trigger.evaluate(falling) == [] and trigger.evaluate(spread) == []


def test_invest_words_with_a_non_valid_handle():
    assert [p["reason"] for p in trigger.evaluate([t(1, 1, "x.desk@mockupi", 9000, "IPO allotment fee")])] == [
        "invest_words_without_valid_handle"
    ]
    assert trigger.evaluate([t(1, 1, "zerobroker.brk@validmock", 9000, "invest SIP")]) == []
    assert trigger.evaluate([t(1, 1, "landlord@mockupi", 30000, "rent")]) == []


def test_at_most_one_prompt_per_campaign_per_customer():
    burst = [
        t(1, 1, "a@mockupi", 5000),
        t(2, 4, "b@mockupi", 9000),
        t(3, 9, "c@mockupi", 20000),
        t(4, 10, "d@mockupi", 40000),
    ]
    assert len(trigger.evaluate(burst)) == 1  # a growing burst is one campaign
    customer = next(c for c in sorted({r["customer_id"] for r in trigger.ledger()}) if trigger.for_customer(c))
    first = trigger.for_customer(customer)[0]
    trigger.acknowledge(customer, first["campaign"])
    assert first["campaign"] not in [p["campaign"] for p in trigger.for_customer(customer)]


def test_payee_reported_after_review_warns_its_other_payers():
    assert trigger.for_customer("SYN-C0011") == []
    suspect_registry.add("zyphrastock.invest@mockupi", "chk-test")
    assert [p["reason"] for p in trigger.for_customer("SYN-C0011")] == ["payee_in_suspect_registry"]
