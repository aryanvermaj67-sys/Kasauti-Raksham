"""CheckResult and Verdict. Mirrors docs/formats/verdict.schema.json. Three outcomes only."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Outcome = Literal["MATCHES", "CONTRADICTS", "NO_RECORD"]
ReasonCode = Literal[
    "HOLDINGS_TOTAL_NONE_FOUND",
    "HOLDINGS_TOTAL_SOME_FOUND",
    "HOLDINGS_TOTAL_ALL_FOUND",
    "HOLDINGS_TOTAL_INCOMPLETE",
    "HOLDING_FOUND",
    "HOLDING_NOT_FOUND_ALL_DEPOSITORIES",
    "HOLDING_QUANTITY_DIFFERS",
    "HOLDING_PARTIAL_COVERAGE",
    "HOLDING_NO_DEMAT",
    "HOLDING_ISIN_UNMAPPED",
    "HOLDING_NAME_AMBIGUOUS",
    "HOLDING_NO_CONSENT",
    "BROKER_ON_SEBI_LIST",
    "BROKER_NOT_ON_SEBI_LIST",
    "BROKER_NEAR_MATCH",
    "BROKER_NOT_FOUND_NOT_CLAIMED",
    "BROKER_REG_NO_MISMATCH",
    "PAYEE_VALID_HANDLE",
    "PAYEE_IN_SUSPECT_REGISTRY",
    "PAYEE_BROKER_NOT_VALID_HANDLE",
    "PAYEE_NO_REGISTRY_HIT",
    "ENDORSEMENT_SOURCE_SAME",
    "ENDORSEMENT_WORDS_CHANGED",
    "ENDORSEMENT_NO_SOURCE",
    "PLATFORM_ON_RBI_ALERT_LIST",
    "PLATFORM_NOT_ON_ALERT_LIST",
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Message(Strict):
    reason_code: ReasonCode
    params: dict[str, Any]


class Verdict(Strict):
    claim_id: str
    claim_type: Literal["holding", "broker", "payee", "endorsement", "platform"]
    outcome: Outcome
    reason_code: ReasonCode
    params: dict[str, Any]
    evidence_ids: list[str]


class CheckResult(Strict):
    check_id: str
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    consent_id: str | None
    created_at: datetime
    summary: list[Message]
    verdicts: list[Verdict]
