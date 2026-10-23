"""Validate docs/formats/examples/*.example.json against their JSON Schemas.

Usage: python scripts/validate_formats.py   (exit 1 on any failure)
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

FORMATS = Path(__file__).resolve().parent.parent / "docs" / "formats"
NAMES = ["claims", "verdict", "record_response", "evidence_pack"]


def main():
    ok = 0
    for name in NAMES:
        schema = json.loads((FORMATS / f"{name}.schema.json").read_text(encoding="utf-8"))
        example = json.loads((FORMATS / "examples" / f"{name}.example.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(example))
        for e in errors:
            print(f"{name}: {e.json_path}: {e.message}")
        ok += not errors
    print(f"validated {ok}/{len(NAMES)} examples")
    return 0 if ok == len(NAMES) else 1


if __name__ == "__main__":
    sys.exit(main())
