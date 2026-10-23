import type { Params } from './i18n.ts'

export type FieldValue = string | number | boolean | null
export type Claim = { id: string; type: 'holding' | 'broker' | 'payee' | 'endorsement' | 'platform'; fields: Record<string, FieldValue> }
export type ClaimSet = {
  artifact_sha256: string
  language: 'en' | 'hi'
  claims: Claim[]
  portfolio_total_inr: number | null
  reader: { provider: string; produced_at: string }
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

// MOCK bank login: the signed-in customer is synthetic case P0001 in data/synthetic/portfolios
export const CUSTOMER = { id: 'SYN-C0001', name: 'Synthetic Customer 0001' }

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

export const runCheck = (claimset: ClaimSet, consentId: string) =>
  post('/api/check', { claimset, customer_id: CUSTOMER.id, consent_id: consentId }).then(body<CheckResult>)

export const logEvent = (kind: 'trusted_contact' | 'bank_callback' | 'still_pay', checkId: string) =>
  post('/api/events', { kind, check_id: checkId, customer_id: CUSTOMER.id }).then(body<{ event_id: string }>)

export async function sha256Hex(file: File) {
  const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer())
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('')
}
