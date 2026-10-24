import type { Params } from './i18n.ts'

export type FieldValue = string | number | boolean | null
export type Claim = { id: string; type: 'holding' | 'broker' | 'payee' | 'endorsement' | 'platform'; fields: Record<string, FieldValue> }
export type ClaimSet = {
  artifact_sha256: string
  language: 'en' | 'hi'
  claims: Claim[]
  portfolio_total_inr: number | null
  reader: { provider: string; produced_at: string; fallback?: boolean }
}
export type Outcome = 'MATCHES' | 'CONTRADICTS' | 'NO_RECORD'
export type Verdict = { claim_id: string; claim_type: string; outcome: Outcome; reason_code: string; params: Params; evidence_ids: string[] }
export type CheckResult = {
  check_id: string
  artifact_sha256: string
  consent_id: string
  summary: { reason_code: string; params: Params }[]
  verdicts: Verdict[]
}
export type Candidate = { isin: string; name: string }

// MOCK bank login: ?customer=SYN-C0028 signs in as that synthetic customer from data/synthetic/portfolios;
// picking a demo scenario signs in as that scenario's customer instead
const asked = new URLSearchParams(window.location.search).get('customer') ?? ''
export const URL_CUSTOMER = /^SYN-C\d{4}$/.test(asked) ? asked : null

export const health = () => fetch('/api/health').then(body<{ ready: boolean; loading: string[] }>)

async function body<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return r.json() as Promise<T>
}

export function readArtifact(file: File) {
  const form = new FormData()
  form.append('file', file)
  return fetch('/api/read', { method: 'POST', body: form }).then(body<ClaimSet>)
}

export const isinCandidates = (name: string) =>
  fetch(`/api/isin/candidates?name=${encodeURIComponent(name)}`)
    .then(body<{ candidates: Candidate[] }>)
    .then((r) => r.candidates)

const post = (url: string, data: unknown) =>
  fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })

/** scope [] means the customer refused the holdings check: registries only, holdings come back NO_RECORD */
export const runCheck = (claimset: ClaimSet, customer: string, consentId: string, scope: string[]) =>
  post('/api/check', { claimset, customer_id: customer, consent_id: consentId, consent_scope: scope }).then(body<CheckResult>)

export const logEvent = (kind: 'trusted_contact' | 'bank_callback' | 'still_pay', checkId: string, customer: string) =>
  post('/api/events', { kind, check_id: checkId, customer_id: customer }).then(body<{ event_id: string }>)

export type Scenario = { id: string; customer_id: string; screenshot: string; video: string | null; payment_request: { payee: string } | null }
export const scenarios = () => fetch('/demo/scenarios').then(body<{ scenarios: Scenario[] }>).then((r) => r.scenarios)
export const demoFile = (url: string) =>
  fetch(url).then(async (r) => new File([await r.blob()], url.split('/').pop()!, { type: r.headers.get('content-type') ?? '' }))

/** What the evidence chain kept of each record a verdict was decided on. */
export type RecordSummary = { source: string; fetched_at: string; mock: boolean; status: string; sha256: string }
export const checkRecords = (checkId: string, customer: string) =>
  fetch(`/api/checks/${checkId}/records?customer_id=${customer}`).then(body<RecordSummary[]>)

/** The customer's evidence pack: the exact bytes and the backend's SHA-256 of them. */
export async function evidencePack(checkId: string, customer: string) {
  const r = await fetch(`/api/checks/${checkId}/pack?customer_id=${customer}`)
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  const blob = await r.blob()
  const pack = JSON.parse(await blob.text()) as { pack_id: string; chain_valid: boolean }
  return { blob, pack, sha256: r.headers.get('X-Pack-SHA256') ?? '' }
}

export type Prompt = { campaign: string; reason: string; payee: string }
export const triggerPrompts = (customerId: string) =>
  fetch(`/api/trigger/${customerId}`)
    .then(body<{ prompts: Prompt[] }>)
    .then((r) => r.prompts)
export const ackPrompt = (customerId: string, campaign: string) => post(`/api/trigger/${customerId}/ack`, { campaign })

// MOCK reviewer login: the role travels in a header; the backend refuses reviewer data to any other role
const asReviewer = { 'X-Role': 'reviewer', 'Content-Type': 'application/json' }
export const review = {
  queue: () => fetch('/api/reviewer/queue', { headers: asReviewer }).then(body<{ check_id: string; customer_id: string; created_at: string }[]>),
  detail: (id: string) => fetch(`/api/reviewer/checks/${id}`, { headers: asReviewer }).then(body<ReviewDetail>),
  decide: (id: string, decision: 'approve' | 'reject', reason: string) =>
    fetch(`/api/reviewer/checks/${id}/${decision}`, { method: 'POST', headers: asReviewer, body: JSON.stringify({ reason }) }).then(
      body<{ registry_added?: { identifier: string }[]; other_customers_who_paid?: string[]; reason?: string }>,
    ),
  pack: (id: string) => fetch(`/api/reviewer/checks/${id}/pack`, { method: 'POST', headers: asReviewer }).then(body<{ pack_id: string; html: string }>),
}
export type ReviewDetail = {
  check: { check_id: string; customer_id: string; status: string }
  claims: Claim[]
  result: CheckResult
  records: Record<string, unknown>[]
  hashes: { seq: number; kind: string; entry_hash: string; prev_hash: string | null }[]
  chain: { valid: boolean; detail: string }
}

export type VideoMatch ={ source_found: boolean; quote?: string; transcript: string }

/** FR-6 source check: the backend stores the result as evidence, keyed by the file's SHA-256. */
export function uploadVideo(file: File) {
  const form = new FormData()
  form.append('file', file)
  return fetch('/api/video', { method: 'POST', body: form }).then(body<{ media_sha256: string; match: VideoMatch }>)
}
