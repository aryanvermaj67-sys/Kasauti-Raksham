"""ClaimSet: what the claim reader extracted. Mirrors docs/formats/claims.schema.json (test_schemas_agree checks it)."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HoldingFields(Strict):
    instrument_name: str
    isin: Annotated[str, Field(pattern=r"^IN[A-Z0-9]{10}$")] | None
    quantity: Annotated[int, Field(ge=0)] | None
    value_inr: Annotated[float, Field(ge=0)] | None


class BrokerFields(Strict):
    name: str
    sebi_reg_no: str | None
    claims_registered: bool


class PayeeFields(Strict):
    upi_id: str | None
    account_no_last4: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None
    ifsc: Annotated[str, Field(pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")] | None
    described_as: Literal["broker", "advisor", "other"]


class EndorsementFields(Strict):
    person: str
    quote: str
    media_sha256: Sha256


class PlatformFields(Strict):
    name: str
    category: Literal["equity", "forex", "crypto", "other"]
    claims_licensed: bool


class HoldingClaim(Strict):
    id: str
    type: Literal["holding"]
    fields: HoldingFields


class BrokerClaim(Strict):
    id: str
    type: Literal["broker"]
    fields: BrokerFields


class PayeeClaim(Strict):
    id: str
    type: Literal["payee"]
    fields: PayeeFields


class EndorsementClaim(Strict):
    id: str
    type: Literal["endorsement"]
    fields: EndorsementFields


class PlatformClaim(Strict):
    id: str
    type: Literal["platform"]
    fields: PlatformFields


Claim = Annotated[
    HoldingClaim | BrokerClaim | PayeeClaim | EndorsementClaim | PlatformClaim, Field(discriminator="type")
]


class Reader(Strict):
    provider: Literal["bedrock", "anthropic", "offline"]
    produced_at: datetime


class ClaimSet(Strict):
    artifact_sha256: Sha256
    language: Literal["en", "hi"]
    claims: list[Claim]
    portfolio_total_inr: Annotated[float, Field(ge=0)] | None
    reader: Reader
