"""Check messages_en.json / messages_hi.json cover every reason_code in verdict.schema.json.

Also checks: both columns present, same {placeholders} in both languages, Hindi entries carry a
needs_native_review true/false flag, and no holdings message hard-codes a depository name.
Usage: python scripts/check_templates.py   (exit 1 on any problem)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "backend" / "app" / "templates"


def placeholders(entry):
    return set(re.findall(r"\{(\w+)\}", entry["app"] + entry["record"]))


def main():
    schema = json.loads((ROOT / "docs" / "formats" / "verdict.schema.json").read_text(encoding="utf-8"))
    codes = schema["$defs"]["reason_code"]["enum"]
    msgs = {
        lang: json.loads((TEMPLATES / f"messages_{lang}.json").read_text(encoding="utf-8"))["reason_codes"]
        for lang in ("en", "hi")
    }
    problems = []
    for lang, m in msgs.items():
        missing = [c for c in codes if not (m.get(c, {}).get("app") and m.get(c, {}).get("record"))]
        problems += [f"{lang}: unknown code {c}" for c in m if c not in codes]
        print(f"{lang}: {len(missing)} missing" + (f" {missing}" if missing else ""))
        problems += [f"{lang}: missing {c}" for c in missing]
    for c in codes:
        if c not in msgs["en"] or c not in msgs["hi"]:
            continue
        if placeholders(msgs["en"][c]) != placeholders(msgs["hi"][c]):
            problems.append(f"{c}: placeholders differ between en and hi")
        if not isinstance(msgs["hi"][c].get("needs_native_review"), bool):  # true until a Hindi reader signs it off
            problems.append(f"hi {c}: needs_native_review must be true or false")
        for lang in msgs:
            e = msgs[lang][c]
            if c.startswith("HOLDING") and re.search(r"CDSL|NSDL", e["app"] + e["record"]):
                problems.append(f"{lang} {c}: hard-coded depository name; use {{depositories}}")
    ui = {lang: json.loads((TEMPLATES / f"messages_{lang}.json").read_text(encoding="utf-8"))["ui"] for lang in msgs}
    keys = {lang: {k for k in u if not k.startswith("_")} for lang, u in ui.items()}
    problems += [f"ui key {k} missing in {lang}" for lang in ui for k in set().union(*keys.values()) - keys[lang]]
    for k in keys["en"] & keys["hi"]:
        if set(re.findall(r"\{(\w+)\}", ui["en"][k])) != set(re.findall(r"\{(\w+)\}", ui["hi"][k])):
            problems.append(f"ui {k}: placeholders differ between en and hi")
    print(f"ui: {len(keys['en'])} strings, {len(keys['en'] ^ keys['hi'])} missing")
    for p in problems:
        print("problem:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
