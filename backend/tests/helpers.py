import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = {
    lang: json.loads((ROOT / "backend" / "app" / "templates" / f"messages_{lang}.json").read_text(encoding="utf-8"))[
        "reason_codes"
    ]
    for lang in ("en", "hi")
}


def renderable(v):
    """Every {placeholder} in both languages' templates must be filled by the verdict's params."""
    for lang, msgs in TEMPLATES.items():
        entry = msgs[v.reason_code]
        missing = set(re.findall(r"\{(\w+)\}", entry["app"] + entry["record"])) - set(v.params)
        assert not missing, f"{v.reason_code} ({lang}) lacks params {missing}"
    return v
