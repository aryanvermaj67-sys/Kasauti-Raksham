import { useEffect, useState } from 'react'
import { review, type ReviewDetail } from '../api.ts'
import { ui, verdictText, type Params } from '../i18n.ts'

const t = (key: string, params?: Params) => ui('en', key, params)
const btn = 'rounded border px-3 py-2 font-semibold'

export default function Reviewer() {
  const [queue, setQueue] = useState<{ check_id: string; customer_id: string; created_at: string }[]>([])
  const [detail, setDetail] = useState<ReviewDetail | null>(null)
  const [reason, setReason] = useState('')
  const [outcome, setOutcome] = useState('')
  const [error, setError] = useState('')

  const load = () => review.queue().then(setQueue).catch((e) => setError(String(e)))
  useEffect(() => {
    load()
  }, [])

  async function open(id: string) {
    setOutcome('')
    setDetail(await review.detail(id))
  }

  async function decide(decision: 'approve' | 'reject') {
    const r = await review.decide(detail!.check.check_id, decision, reason)
    setOutcome(
      decision === 'approve'
        ? `${t('reviewer_added', { payees: (r.registry_added ?? []).map((a) => a.identifier) })} ${t('reviewer_others', { customers: r.other_customers_who_paid ?? [] })}`
        : t('reviewer_rejected', { reason: r.reason }),
    )
    load()
  }

  async function exportPack() {
    const p = await review.pack(detail!.check.check_id)
    setOutcome(t('reviewer_pack_done', { pack_id: p.pack_id, html: p.html }))
  }

  return (
    <main className="mx-auto max-w-4xl space-y-4 p-6 text-slate-900">
      <header className="flex items-baseline justify-between">
        <h1 className="text-2xl font-bold">{t('reviewer_title')}</h1>
        <span className="rounded bg-amber-500 px-2 py-0.5 text-sm font-bold text-white">{t('reviewer_role_note')}</span>
      </header>
      {error && <p className="text-red-700">{t('error', { error })}</p>}
      <section>
        <h2 className="font-semibold">{t('reviewer_queue')}</h2>
        {queue.length === 0 && <p data-testid="queue-empty">{t('reviewer_empty')}</p>}
        <ul className="mt-2 space-y-1">
          {queue.map((q) => (
            <li key={q.check_id}>
              <button data-testid={`queue-${q.check_id}`} className="underline" onClick={() => open(q.check_id)}>
                {`${q.check_id} · ${t('reviewer_customer', { customer: q.customer_id })} · ${q.created_at.slice(0, 16)}`}
              </button>
            </li>
          ))}
        </ul>
      </section>

      {detail && (
        <section data-testid="review-detail" className="space-y-4 rounded-lg border bg-white p-4">
          <h2 className="text-lg font-bold">{`${detail.check.check_id} · ${t('reviewer_customer', { customer: detail.check.customer_id })}`}</h2>
          <p data-testid="chain-status" className={detail.chain.valid ? 'text-green-700' : 'text-red-700'}>
            {t(detail.chain.valid ? 'reviewer_chain_ok' : 'reviewer_chain_bad', { detail: detail.chain.detail })}
          </p>
          <h3 className="font-semibold">{t('reviewer_verdicts')}</h3>
          <ul className="space-y-1 text-sm">
            {[...detail.result.summary, ...detail.result.verdicts].map((v) => {
              const text = verdictText('en', v.reason_code, v.params)
              return <li key={`${v.reason_code}-${'claim_id' in v ? v.claim_id : 'total'}`}>{`${'outcome' in v ? v.outcome : ''} ${text.app} | ${text.record}`}</li>
            })}
          </ul>
          <h3 className="font-semibold">{t('reviewer_claims')}</h3>
          <pre className="overflow-x-auto bg-slate-50 p-2 text-xs">{JSON.stringify(detail.claims, null, 1)}</pre>
          <h3 className="font-semibold">{t('reviewer_records')}</h3>
          <ul className="text-xs">
            {detail.records.map((r) => (
              <li key={String(r.sha256)}>{`${r.source} · ${r.status}${r.mock ? ' · MOCK' : ''} · ${r.sha256}`}</li>
            ))}
          </ul>
          <h3 className="font-semibold">{t('reviewer_hashes')}</h3>
          <ol className="text-xs [overflow-wrap:anywhere]">
            {detail.hashes.map((h) => (
              <li key={h.seq}>{`${h.seq} ${h.kind} ${h.entry_hash}`}</li>
            ))}
          </ol>
          {detail.check.status === 'open' && (
            <div className="space-y-2">
              <label className="block text-sm">
                {t('reviewer_reason')}
                <textarea data-testid="reason" className="mt-1 w-full rounded border p-2" value={reason} onChange={(e) => setReason(e.target.value)} />
              </label>
              <div className="flex gap-2">
                <button data-testid="approve" className={`${btn} bg-red-700 text-white`} onClick={() => decide('approve')}>
                  {t('reviewer_approve')}
                </button>
                <button data-testid="reject" className={btn} disabled={!reason.trim()} onClick={() => decide('reject')}>
                  {t('reviewer_reject')}
                </button>
              </div>
            </div>
          )}
          <button data-testid="export-pack" className={btn} onClick={exportPack}>
            {t('reviewer_pack')}
          </button>
          {outcome && <p data-testid="review-outcome" className="rounded bg-slate-100 p-2 text-sm [overflow-wrap:anywhere]">{outcome}</p>}
        </section>
      )}
    </main>
  )
}
