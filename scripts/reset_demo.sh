#!/usr/bin/env sh
# Reset the demo to its seed state (see scripts/reset_demo.py).
cd "$(dirname "$0")/.." && exec python scripts/reset_demo.py "$@"
