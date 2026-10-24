"""Route each confirmed claim to its record, then to its rule."""

import uuid
from datetime import datetime

from app.connectors import aa_mock, footage_index, isin_master, rbi, sebi, suspect_registry, upi
from app.schemas.claims import ClaimSet
from app.schemas.evidence import IST
from app.schemas.verdict import CheckResult
from app.verdict import rules


def map_isins(claimset: ClaimSet):
    """FR-2.7: fill missing ISINs from the NSE/BSE lists; unmapped names stay null for the customer to fix."""
    cs = claimset.model_copy(deep=True)
    mappings = {}
    for c in cs.claims:
        if c.type == "holding":
            rec = isin_master.lookup(c.fields.instrument_name, c.fields.isin)  # also says if a shown ISIN is listed
            c.fields.isin = c.fields.isin or rec.payload["isin"]
            mappings[c.id] = rec
    return cs, mappings


def run_check(claimset: ClaimSet, customer_id: str, consent_id: str, scope=aa_mock.DEPOSITORIES):
    cs, mappings = map_isins(claimset)
    records = list(mappings.values())
    aa = aa_mock.fetch(customer_id, consent_id, scope) if any(c.type == "holding" for c in cs.claims) else []
    records += aa
    verdicts = []
    for c in cs.claims:
        f = c.fields
        if c.type == "holding":
            v = rules.holding(c, aa, mappings.get(c.id))
        elif c.type == "broker":
            rec = sebi.lookup(f.name, f.sebi_reg_no)
            records.append(rec)
            v = rules.broker(c, rec)
        elif c.type == "payee":
            reg = suspect_registry.lookup(f.upi_id or rules.payee_label(f))
            u = upi.check(f.upi_id) if f.upi_id else None
            records += [r for r in (reg, u) if r]
            v = rules.payee(c, reg, u)
        elif c.type == "endorsement":
            rec = footage_index.lookup(f.media_sha256)  # stored by POST /api/video; None -> NO_RECORD
            records += [rec] if rec else []
            v = rules.endorsement(c, rec)
        else:
            rec = rbi.lookup(f.name)
            records.append(rec)
            v = rules.platform(c, rec)
        verdicts.append(v)
    total = cs.portfolio_total_inr
    if total is None:
        values = [c.fields.value_inr for c in cs.claims if c.type == "holding" and c.fields.value_inr is not None]
        total = sum(values) if values else None
    result = CheckResult(
        check_id=f"chk-{uuid.uuid4().hex[:12]}",
        artifact_sha256=cs.artifact_sha256,
        consent_id=consent_id,
        created_at=datetime.now(IST),
        summary=rules.holdings_summary(verdicts, total, aa),
        verdicts=verdicts,
    )
    return result, records
