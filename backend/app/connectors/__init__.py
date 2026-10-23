from pathlib import Path

DATA = Path(__file__).resolve().parents[3] / "data"


def need(path: Path) -> Path:
    """Registries are local copies (git-ignored); fail loudly instead of inventing data."""
    if not path.exists():
        raise FileNotFoundError(f"{path} missing: run python scripts/fetch_registries.py (see data/SOURCES.md)")
    return path
