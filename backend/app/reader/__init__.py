"""Claim reader: artifact bytes -> ClaimSet, chosen by LLM_PROVIDER. It extracts claims; it never sets a verdict."""

import hashlib
import os

from app.connectors import DATA
from app.reader import offline
from app.schemas.claims import ClaimSet

CACHE = DATA / "demo_cache"


def read(image: bytes) -> ClaimSet:
    sha = hashlib.sha256(image).hexdigest()
    provider = os.environ.get("LLM_PROVIDER", "cache")
    if provider == "cache":  # replays a stored reader output, keyed by the file's SHA-256; nothing else is cached
        path = CACHE / f"{sha}.json"
        if not path.exists():
            raise LookupError(f"no cached ClaimSet for {sha}")
        return ClaimSet.model_validate_json(path.read_text(encoding="utf-8"))
    if provider == "offline":
        return offline.read(image, sha)
    raise NotImplementedError(f"LLM_PROVIDER={provider} is not built yet; use cache or offline")


def save_to_cache(cs: ClaimSet):
    path = CACHE / f"{cs.artifact_sha256}.json"
    path.write_text(cs.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path
