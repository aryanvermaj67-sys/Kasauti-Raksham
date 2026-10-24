"""Deterministic verdict rules (PRD FR-5). Inputs are confirmed claims and connector RecordResponses only.

The claim reader (LLM or OCR) never reaches this module, so text inside an artifact cannot set an outcome.
Three outcomes only: MATCHES, CONTRADICTS, NO_RECORD.
"""

from app.comparators.holdings import compare
from app.connectors.names import normalize
from app.schemas.verdict import Message, Verdict

ALL_DEPOSITORIES = ("CDSL", "NSDL")


def _v(claim, outcome, reason, params, records):
    return Verdict(
        claim_id=claim.id,
        claim_type=claim.type,
        outcome=outcome,
        reason_code=reason,
        params=params,
        evidence_ids=[r.sha256 for r in records if r is not None],
    )


def holding(claim, aa_records, mapping=None):
    f = claim.fields
    params = {"instrument_name": f.instrument_name, "quantity": f.quantity}
    evidence = [*aa_records, mapping]
    if not aa_records:  # the customer refused the holdings check: nothing was compared, so never CONTRADICTS
        return _v(claim, "NO_RECORD", "HOLDING_NO_CONSENT", params, [mapping])
    if f.isin is None:
        count = mapping.payload["candidates"] if mapping else 0
        if count > 1:  # the customer skipped choosing among several listed securities
            return _v(claim, "NO_RECORD", "HOLDING_NAME_AMBIGUOUS", params | {"candidate_count": count}, evidence)
        return _v(claim, "NO_RECORD", "HOLDING_ISIN_UNMAPPED", params, evidence)
    facts = compare(f.isin, aa_records)
    failed = [d for d in ALL_DEPOSITORIES if d not in facts["ok_depositories"]]
    units = facts["units_found"]
    params |= {"isin": f.isin, "depositories": facts["ok_depositories"], "failed_depositories": failed}
    if units and (f.quantity is None or units == f.quantity):
        return _v(claim, "MATCHES", "HOLDING_FOUND", params | {"quantity": units}, evidence)
    if mapping and not mapping.payload.get("listed", True):
        # an ISIN on neither list is likelier a misread (O for 0) than a security: its absence proves nothing
        return _v(claim, "NO_RECORD", "HOLDING_ISIN_UNMAPPED", params, evidence)
    if failed:  # a depository we could not read may hold it: partial coverage is never CONTRADICTS
        return _v(claim, "NO_RECORD", "HOLDING_PARTIAL_COVERAGE", params, evidence)
    if units:
        return _v(claim, "CONTRADICTS", "HOLDING_QUANTITY_DIFFERS", params | {"record_quantity": units}, evidence)
    if not facts["has_account"]:
        return _v(claim, "NO_RECORD", "HOLDING_NO_DEMAT", params, evidence)
    return _v(claim, "CONTRADICTS", "HOLDING_NOT_FOUND_ALL_DEPOSITORIES", params, evidence)


def holdings_summary(verdicts, portfolio_total_inr, aa_records):
    hv = [v for v in verdicts if v.claim_type == "holding"]
    if not hv or not aa_records:  # no consent: each holding row already says nothing was compared
        return []
    ok = [r.payload["depository"] for r in aa_records if r.status == "OK"]
    failed = [d for d in ALL_DEPOSITORIES if d not in ok]
    found = sum(v.outcome == "MATCHES" for v in hv)
    # shortcut: unmapped names count as "not found" in the total; the confirm step asks the customer to fix them first
    if failed:
        code = "HOLDINGS_TOTAL_INCOMPLETE"
    else:
        code = {0: "HOLDINGS_TOTAL_NONE_FOUND", len(hv): "HOLDINGS_TOTAL_ALL_FOUND"}.get(
            found, "HOLDINGS_TOTAL_SOME_FOUND"
        )
    params = {
        "claimed_count": len(hv),
        "found_count": found,
        "claimed_value_inr": portfolio_total_inr,
        "depositories": ok,
        "failed_depositories": failed,
    }
    return [Message(reason_code=code, params=params)]


def broker(claim, sebi_record):
    f, p = claim.fields, sebi_record.payload
    q = normalize(f.name)
    params = {"name": f.name}
    ev = [sebi_record]
    if f.sebi_reg_no:
        # The number must belong to this name: a borrowed registration number is the classic impersonation.
        reg = p["reg_no_entry"]
        names = {normalize(reg["name"]), normalize(reg["trade_name"] or reg["name"])} if reg else set()
        if q in names:
            return _v(claim, "MATCHES", "BROKER_ON_SEBI_LIST", params | {"sebi_reg_no": reg["reg_no"]}, ev)
        if reg and reg["within_one_typo"]:
            return _v(
                claim,
                "NO_RECORD",
                "BROKER_NEAR_MATCH",
                params | {"near_name": reg["name"], "near_reg_no": reg["reg_no"]},
                ev,
            )
        if reg or p["exact"]:  # the number belongs to another firm, or this firm is listed under another number
            return _v(claim, "CONTRADICTS", "BROKER_REG_NO_MISMATCH", params | {"claimed_reg_no": f.sebi_reg_no}, ev)
    if p["exact"]:
        return _v(claim, "MATCHES", "BROKER_ON_SEBI_LIST", params | {"sebi_reg_no": p["exact"]["reg_no"]}, ev)
    if p["near"]:  # within one typo of a registered firm, but not its exact name: ambiguous
        return _v(
            claim,
            "NO_RECORD",
            "BROKER_NEAR_MATCH",
            params | {"near_name": p["near"]["name"], "near_reg_no": p["near"]["reg_no"]},
            ev,
        )
    if f.claims_registered:
        return _v(claim, "CONTRADICTS", "BROKER_NOT_ON_SEBI_LIST", params, ev)
    return _v(claim, "NO_RECORD", "BROKER_NOT_FOUND_NOT_CLAIMED", params, ev)


def payee_label(fields):
    if fields.upi_id:
        return fields.upi_id
    return f"XXXX{fields.account_no_last4 or ''}" + (f" ({fields.ifsc})" if fields.ifsc else "")


def payee(claim, registry_record, upi_record=None):
    f = claim.fields
    params = {"payee": payee_label(f)}
    ev = [registry_record, upi_record]
    if registry_record.payload["hit"]:
        return _v(claim, "CONTRADICTS", "PAYEE_IN_SUSPECT_REGISTRY", params, ev)
    if upi_record and upi_record.payload["valid_handle_format"]:
        return _v(claim, "MATCHES", "PAYEE_VALID_HANDLE", params, ev)
    if f.upi_id and f.described_as == "broker":
        return _v(claim, "CONTRADICTS", "PAYEE_BROKER_NOT_VALID_HANDLE", params, ev)
    return _v(claim, "NO_RECORD", "PAYEE_NO_REGISTRY_HIT", params, ev)


def endorsement(claim, footage_record=None):
    """footage payload from the video comparator: source_found, transcript_same, changed_ranges, original_quote."""
    f = claim.fields
    params = {"person": f.person, "quote": f.quote}
    m = footage_record.payload if footage_record and footage_record.status == "OK" else {}
    if not m.get("source_found"):  # missing source is not proof: never MATCHES, never "real"
        return _v(claim, "NO_RECORD", "ENDORSEMENT_NO_SOURCE", params, [footage_record])
    params |= {"source_clip": m.get("source_clip")}
    if m["transcript_same"]:
        return _v(claim, "MATCHES", "ENDORSEMENT_SOURCE_SAME", params, [footage_record])
    params |= {"time_ranges": m["changed_ranges"], "original_quote": m["original_quote"]}
    return _v(claim, "CONTRADICTS", "ENDORSEMENT_WORDS_CHANGED", params, [footage_record])


def platform(claim, rbi_record):
    params = {"name": claim.fields.name}
    if rbi_record.payload["match"]:
        return _v(claim, "CONTRADICTS", "PLATFORM_ON_RBI_ALERT_LIST", params, [rbi_record])
    return _v(claim, "NO_RECORD", "PLATFORM_NOT_ON_ALERT_LIST", params, [rbi_record])  # never MATCHES in the MVP
