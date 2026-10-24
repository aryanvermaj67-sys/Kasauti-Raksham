#!/usr/bin/env sh
# Run every check. --quick: tests, lint, build and the EXAMPLE set check (no servers, no browser, no models).
# Full: also the offline browser demo (scripts/demo.py) and the validation run on the EXAMPLE set.
set -e
cd "$(dirname "$0")/.."
step() { printf '\n==== %s\n' "$*"; }
step backend tests;      (cd backend && python -m pytest -q)
step backend lint;       (cd backend && python -m ruff check . && python -m ruff format --check .)
step templates;          python scripts/check_templates.py
step frontend;           (cd frontend && npm run build && npm run lint && npm test)
step "app code has no demo figures"; ! grep -rniE "Zyphra|39800000|3,98,00,000|3\.98 cr" frontend/src --include=*.tsx --include=*.ts --exclude=*.test.ts
step example frozen set; python scripts/check_frozen.py data/frozen_example --example
if [ "$1" != "--quick" ]; then
  step offline demo;     python scripts/demo.py
  step validation;       python scripts/run_frozen.py --example || echo "(example labels are illustrations; see docs/VALIDATION_EXAMPLE.md)"
fi
step "ALL CHECKS PASSED${1:+ ($1)}"
