"""Evidence pack export (FR-9.2): JSON in docs/formats/evidence_pack.schema.json plus a readable HTML hash listing.

The HTML is a hash listing to support a certificate (e.g. under BSA Section 63(4)); it is not itself a certificate.
"""

import html
from datetime import datetime

from app.connectors import DATA
from app.evidence import hashchain
from app.schemas.evidence import IST, EvidencePack

PACKS = DATA / "runtime" / "packs"


def pack_id(check_id: str) -> str:
    return f"pack-{check_id}"


def export(check_id: str, role: str) -> dict:
    ok, why = hashchain.verify_chain(check_id)
    entries = hashchain.entries(check_id, role)
    pack = EvidencePack(
        pack_id=pack_id(check_id), check_id=check_id, exported_at=datetime.now(IST), chain_valid=ok, entries=entries
    )
    PACKS.mkdir(parents=True, exist_ok=True)
    js, page = PACKS / f"{pack.pack_id}.json", PACKS / f"{pack.pack_id}.html"
    js.write_text(pack.model_dump_json(indent=1), encoding="utf-8")
    rows = "".join(
        f"<tr><td>{e['seq']}</td><td>{html.escape(e['kind'])}</td><td>{html.escape(e['recorded_at'])}</td>"
        f"<td><code>{e['content_sha256']}</code></td><td><code>{e['prev_hash'] or '-'}</code></td>"
        f"<td><code>{e['entry_hash']}</code></td></tr>"
        for e in entries
    )
    page.write_text(
        f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Evidence pack {pack.pack_id}</title>
<style>body{{font-family:Arial,sans-serif;margin:24px;color:#111}}table{{border-collapse:collapse;font-size:12px}}
td,th{{border:1px solid #bbb;padding:4px 6px;vertical-align:top}}code{{word-break:break-all}}
.ok{{color:#0a6b2d}}.bad{{color:#b00020}}</style></head><body>
<h1>Kasauti evidence pack {pack.pack_id}</h1>
<p>Hash listing to support a certificate. This page is not a legal certificate; a certificate (for example under
BSA Section 63(4)) must be issued separately by the responsible person.</p>
<p>Check {html.escape(check_id)} &middot; exported {pack.exported_at.isoformat()}
&middot; MOCK data (synthetic customer)</p>
<p class="{"ok" if ok else "bad"}">
<b>Chain verification: {"PASSED" if ok else "FAILED"}</b> ({html.escape(why)})</p>
<table><tr><th>#</th><th>Kind</th><th>Recorded at</th><th>Content SHA-256</th>
<th>Previous hash</th><th>Entry hash</th></tr>
{rows}</table>
<p>Full entries (with summaries) are in {js.name}. Depository holdings are not included: only the record hash and
which claimed ISINs were found.</p></body></html>
""",
        encoding="utf-8",
    )
    return {"pack_id": pack.pack_id, "json": str(js), "html": str(page), "chain_valid": ok, "detail": why}
