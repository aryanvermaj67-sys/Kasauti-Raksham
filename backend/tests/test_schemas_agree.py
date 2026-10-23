"""Pydantic models in app/schemas agree with docs/formats/*.schema.json."""

import json
import typing

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from app.schemas import claims, evidence, verdict
from tests.helpers import ROOT

FORMATS = ROOT / "docs" / "formats"
PAIRS = {
    "claims": claims.ClaimSet,
    "verdict": verdict.CheckResult,
    "record_response": evidence.RecordResponse,
    "evidence_pack": evidence.EvidencePack,
}


def load(name):
    return json.loads((FORMATS / f"{name}.schema.json").read_text(encoding="utf-8"))


def same_shape(model, schema_obj):
    assert set(model.model_fields) == set(schema_obj["properties"]), model.__name__
    required = {n for n, f in model.model_fields.items() if f.is_required()}
    assert required == set(schema_obj["required"]), model.__name__


@pytest.mark.parametrize("name", PAIRS)
def test_example_round_trips_through_model_and_schema(name):
    model, schema = PAIRS[name], load(name)
    example = json.loads((FORMATS / "examples" / f"{name}.example.json").read_text(encoding="utf-8"))
    dumped = model.model_validate(example).model_dump(mode="json")
    assert not list(Draft202012Validator(schema).iter_errors(dumped))
    same_shape(model, schema)


def test_nested_shapes_and_enums_agree():
    c, v, e = load("claims"), load("verdict"), load("evidence_pack")
    for t, fields in [
        ("holding", claims.HoldingFields),
        ("broker", claims.BrokerFields),
        ("payee", claims.PayeeFields),
        ("endorsement", claims.EndorsementFields),
        ("platform", claims.PlatformFields),
    ]:
        same_shape(fields, c["$defs"][t]["properties"]["fields"])
    same_shape(claims.Reader, c["properties"]["reader"])
    same_shape(verdict.Verdict, v["$defs"]["verdict"])
    same_shape(verdict.Message, v["$defs"]["message"])
    same_shape(evidence.EvidenceEntry, e["$defs"]["entry"])
    assert list(typing.get_args(verdict.ReasonCode)) == v["$defs"]["reason_code"]["enum"]
    assert (
        list(typing.get_args(verdict.Outcome))
        == v["$defs"]["outcome"]["enum"]
        == ["MATCHES", "CONTRADICTS", "NO_RECORD"]
    )
    provider = claims.Reader.model_fields["provider"].annotation
    assert list(typing.get_args(provider)) == c["properties"]["reader"]["properties"]["provider"]["enum"]


def test_reader_output_cannot_carry_a_verdict():
    example = json.loads((FORMATS / "examples" / "claims.example.json").read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        claims.ClaimSet.model_validate(example | {"verdict": "MATCHES"})
    assert list(Draft202012Validator(load("claims")).iter_errors(example | {"verdict": "MATCHES"}))
