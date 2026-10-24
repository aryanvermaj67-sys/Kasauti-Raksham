# UI integration: the incoming design as the customer app

The design export (kept locally in `ui_incoming/`, git-ignored, never run) was a static prototype: every screen read
`mockData.ts`, nothing called a backend, fonts and icons came from Google Fonts, and its outcome words (ALTERED,
PARTIAL MATCH, HIGH DISCREPANCY, "synthetic audio") broke the three-outcome rule. We kept its visual design and
rebuilt every screen on the real pipeline. Design reference: `docs/design/reference/` (spec + two PNGs).

## The 8 phone steps and what each one calls

| # | Step | Shows | Endpoint(s) | New? |
|---|---|---|---|---|
| 1 | Payment | demo scenario picker, payee (from the ad), amount typed by the customer, FR-1.2 prompt | `GET /demo/scenarios`, `GET /api/trigger/{customer}`, `POST /api/trigger/{customer}/ack`, `GET /api/health` | `/demo/scenarios` added |
| 2 | Upload | the scenario's screenshot (+ dev clip) or the customer's own file; read / video progress from the calls themselves | `GET /demo/files/{name}`, `POST /api/read`, `POST /api/video` | `/demo/files` added |
| 3 | Confirm | the claims the reader returned; edit, remove, add; ISIN picker when a name is ambiguous | `GET /api/isin/candidates` | — |
| 4 | Consent | MOCK AA consent naming CDSL and NSDL, OTP; **Refuse** checks registries only | `POST /api/check` with `consent_scope` `["CDSL","NSDL"]` or `[]` | rule `HOLDING_NO_CONSENT` added |
| 5 | Checking | each stage turns "done" when its call returns (no timers); the sources of the records used | `POST /api/check`, `GET /api/checks/{id}/records` | `/records` added |
| 6 | Result | summary, then each claim beside its record text, outcome chip, record source, `fetched_at`, MOCK/public label; read-aloud if a voice for the language exists | (data from step 5) | — |
| 7 | Action | 1930 complaint pre-filled from templates; trusted contact, bank callback, "I still want to pay" (MOCK, logged) | `POST /api/events` | — |
| 8 | Pack | downloads the hashed evidence pack; shows its pack id, the SHA-256 of the downloaded bytes and the chain check | `GET /api/checks/{id}/pack` (header `X-Pack-SHA256`) | added |

`/api/checks/{id}/records` and `/pack` answer only for the customer who ran the check (MOCK login: the customer id
stands in for a session).

## Rules the port follows

- Outcomes are `MATCHES`, `CONTRADICTS`, `NO_RECORD` only, shown as "MATCHES THE RECORD", "CONTRADICTS THE RECORD",
  "NO RECORD FOUND". Every sentence comes from `backend/app/templates/messages_{en,hi}.json` by key or reason code.
- No result, claim, balance, name or number is written in `frontend/src` (`src/outcomes.test.ts`,
  `src/no-hardcoded-text.test.ts`, and the demo-figures grep in `scripts/verify_all.sh`).
- Offline: Inter and Noto Sans Devanagari are bundled (`@fontsource`), icons are `lucide-react`. Removed: `@google/genai`,
  `express`, `dotenv`, `GEMINI_API_KEY`, `metadata.json`, the Google Fonts and Material Symbols links.
- Design tokens (spec colours, 4 px radius, tabular numerals, 44 px touch targets, 19 px large-text mode) are in
  `frontend/src/index.css`. The status chip shows `/api/health`; while models load it says "Preparing" and Check is off.
- Routes: `/app` (customer), `/reviewer` (`/console` redirects there), `/present` (dual view).

## Proof

`python scripts/ui_screens.py` (also run by `scripts/demo.py`): 3 scenarios x EN/HI x 8 steps = 48 screenshots in
`docs/screens/ui/`, every non-localhost request blocked and counted (0), and a canvas check for missing-glyph boxes on
every Hindi screen (0 of 24).
