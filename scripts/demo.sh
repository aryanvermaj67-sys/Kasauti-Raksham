#!/usr/bin/env sh
# Offline demo run (see scripts/demo.py). Pass --cpu to hide the GPU.
cd "$(dirname "$0")/.." && exec python scripts/demo.py "$@"
