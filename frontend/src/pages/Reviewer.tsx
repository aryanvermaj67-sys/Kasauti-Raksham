import { CircleCheck, CircleAlert } from 'lucide-react'
import { useEffect, useState } from 'react'
import { cases, review, stats, type Case, type Outcome, type ReviewDetail, type Stats } from '../api.ts'
import Header, { useHealth, useLarge } from '../components/Header.tsx'
import OutcomeChip from '../components/Outcome.tsx'
import { ui, verdictText, type Lang, type Params } from '../i18n.ts'
import { btn, btn2 } from './CustomerApp.tsx'

const STATES = ['new', 'in_review', 'approved', 'rejected'] as const
const card = 'rounded-box border border-line bg-white p-4'
const startLang = (new URLSearchParams(window.location.search).get('lang') === 'hi' ? 'hi' : 'en') as Lang

export default function Reviewer() {
  const [lang, setLang] = useState<Lang>(startLang)
  const [large, setLarge] = useLarge()
  const status = useHealth()
  const [tab, setTab] = useState<(typeof STATES)[number]>('new')
  const [all, setAll] = useState<Record<string, Case[]>>({})
  const [st, setSt] = useState<Stats | null>(null)
  const [detail, setDetail] = useState<ReviewDetail | null>(null)
  const [reason, setReason] = useState('')
  const [outcome, setOutcome] = useState('')
  const [error, setError] = useState('')
  const t = (key: string, params?: Params) => ui(lang, key, params)

  // polled, so a check made on the phone (or in /present) shows up here through the backend
  useEffect(() => {
    let stop = false
    const load = () =>
      Promise.all([cases().then(setAll), stats().then(setSt)])
        .catch((e) => setError(String(e)))
        .finally(() => !stop && setTimeout(load, 2000))
    load()
    return () => {
      stop = true
    }
  }, [])

  async function open(id: string) {
    setOutcome('')
    setReason('')
    setDetail(await review.detail(id))
  }

  async function decide(decision: 'approve' | 'reject') {
    const r = await review.decide(detail!.check.check_id, decision, reason)
    setOutcome(
      decision === 'approve'
        ? `${t('reviewer_added', { payees: (r.registry_added ?? []).map((a) => a.identifier) })} ${t('reviewer_others', { customers: r.other_customers_who_paid ?? [] })}`
        : t('reviewer_rejected', { reason: r.reason }),
    )
    setDetail(await review.detail(detail!.check.check_id)) // the decision is now the chain's last entry
  }

  async function exportPack() {
    const p = await review.pack(detail!.check.check_id)
    setOutcome(t('reviewer_pack_done', { pack_id: p.pack_id, html: p.html }))
  }

  const sources = (ids: string[]) => (detail?.records ?? []).filter((r) => ids.includes(r.sha256))
  const payees = (detail?.claims ?? []).filter((c) => c.type === 'payee')

  return (
    <div lang={lang} className="min-h-screen bg-canvas">
      <Header lang={lang} setLang={setLang} large={large} setLarge={setLarge} status={status} onReset={() => setDetail(null)} />
      <main className="mx-auto max-w-[1280px] space-y-4 p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-2xl font-bold">{t('console_title')}</h2>
          <span className="rounded-box border border-ink px-2 py-0.5 text-sm font-bold">{t('reviewer_role_note')}</span>
        </div>
        {error && <p className="text-contra">{t('error', { error })}</p>}

        {st && (
          <section data-testid="stats" className="grid gap-2 md:grid-cols-3">
            <div className={card}>
              <p className="font-semibold">{t('stat_prompts', { n: st.prompt_rate.per_1000 })}</p>
              <p className="text-sm text-muted">{t('stat_prompts_label')}</p>
            </div>
            <div className={card}>
              <p className="font-semibold">{t('stat_outcomes', { checks: st.checks })}</p>
              <ul className="mt-1 space-y-1">
                {(Object.entries(st.outcomes) as [Outcome, number][]).map(([o, n]) => (
                  <li key={o} className="flex items-center gap-2">
                    <OutcomeChip outcome={o} lang={lang} /> <span className="font-semibold">{n}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className={card}>
              <p className="font-semibold">
                {st.median_latency_s === null ? t('stat_latency_none') : t('stat_latency', { s: st.median_latency_s, n: st.latency_samples })}
              </p>
            </div>
          </section>
        )}

        <section className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-1" role="tablist">
              {STATES.map((s) => (
                <button key={s} role="tab" aria-selected={tab === s} data-testid={`tab-${s}`} className={tab === s ? btn : btn2} onClick={() => setTab(s)}>
                  {t(`cases_${s}`)} {all[s]?.length ?? 0}
                </button>
              ))}
            </div>
            {(all[tab] ?? []).length === 0 && <p data-testid="queue-empty">{t('reviewer_empty')}</p>}
            <ul className="space-y-1">
              {(all[tab] ?? []).map((c) => (
                <li key={c.check_id}>
                  <button
                    data-testid={`queue-${c.check_id}`}
                    className={`${btn2} justify-start text-left text-sm ${detail?.check.check_id === c.check_id ? 'border-ink' : ''}`}
                    onClick={() => open(c.check_id)}
                  >
                    {c.check_id} · {c.customer_id}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {detail && (
            <section data-testid="review-detail" className="space-y-4">
              <div className={card}>
                <p className="font-semibold [overflow-wrap:anywhere]">
                  {t('case_header', { check_id: detail.check.check_id, customer: detail.check.customer_id, created_at: (all[tab] ?? []).find((c) => c.check_id === detail.check.check_id)?.created_at })}
                </p>
                <p data-testid="chain-status" className={`mt-2 inline-flex items-center gap-1 font-semibold ${detail.chain.valid ? 'text-match' : 'text-contra'}`}>
                  {detail.chain.valid ? <CircleCheck size={16} aria-hidden /> : <CircleAlert size={16} aria-hidden />}
                  {t(detail.chain.valid ? 'reviewer_chain_ok' : 'reviewer_chain_bad', { detail: detail.chain.detail })}
                </p>
              </div>

              {payees.length > 0 && (
                <div data-testid="target" className={card}>
                  <h3 className="font-semibold">{t('target_title')}</h3>
                  {payees.map((p) => (
                    <p key={p.id} className="font-mono [overflow-wrap:anywhere]">
                      {String(p.fields.upi_id ?? p.fields.account_no_last4 ?? '')}
                    </p>
                  ))}
                </div>
              )}

              <div data-testid="matrix" className={`${card} overflow-x-auto`}>
                <h3 className="mb-2 font-semibold">{t('matrix_title')}</h3>
                <table className="w-full text-left text-sm">
                  <thead className="text-xs text-muted">
                    <tr>
                      <th className="p-2">{t('matrix_claim')}</th>
                      <th className="p-2">{t('matrix_record')}</th>
                      <th className="p-2">{t('matrix_source')}</th>
                      <th className="p-2">{t('matrix_determination')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.result.verdicts.map((v) => {
                      const m = verdictText(lang, v.reason_code, v.params)
                      return (
                        <tr key={v.claim_id} className="border-t border-line align-top">
                          <td className="p-2">{m.app}</td>
                          <td className="p-2">{m.record}</td>
                          <td className="p-2 text-xs">
                            {sources(v.evidence_ids).map((r) => (
                              <p key={r.sha256}>
                                {r.source} · {t(r.mock ? 'record_mock' : 'record_public')}
                              </p>
                            ))}
                          </td>
                          <td className="p-2">
                            <OutcomeChip outcome={v.outcome} lang={lang} />
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {detail.network.length > 0 && (
                <div data-testid="network" className={card}>
                  <h3 className="font-semibold">{t('network_title')}</h3>
                  {detail.network.map((n) => (
                    <div key={n.payee} className="mt-2 text-sm [overflow-wrap:anywhere]">
                      <p>{n.registry_hit ? t('network_hit', { payee: n.payee, added_on: n.registry_hit.added_on }) : t('network_no_hit', { payee: n.payee })}</p>
                      <p>{t('network_payers', { payers: n.ledger_payers })}</p>
                    </div>
                  ))}
                </div>
              )}

              {detail.check.status === 'open' && (
                <div className={`${card} space-y-2`}>
                  <label className="block">
                    <span className="text-sm text-muted">{t('reviewer_reason')}</span>
                    <textarea data-testid="reason" className="mt-1 w-full rounded-box border border-line-2 p-2" value={reason} onChange={(e) => setReason(e.target.value)} />
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button data-testid="approve" className={btn} onClick={() => decide('approve')}>
                      {t('reviewer_approve')}
                    </button>
                    <button data-testid="reject" className={btn2} disabled={!reason.trim()} onClick={() => decide('reject')}>
                      {t('reviewer_reject')}
                    </button>
                  </div>
                </div>
              )}
              <button data-testid="export-pack" className={btn2} onClick={exportPack}>
                {t('reviewer_pack')}
              </button>
              {outcome && <p data-testid="review-outcome" className="rounded-box border border-line bg-panel p-2 text-sm [overflow-wrap:anywhere]">{outcome}</p>}

              <div data-testid="audit" className={`${card} overflow-x-auto`}>
                <h3 className="mb-2 font-semibold">{t('audit_title')}</h3>
                <table className="w-full text-left text-xs">
                  <thead className="text-muted">
                    <tr>
                      <th className="p-1">{t('audit_seq')}</th>
                      <th className="p-1">{t('audit_kind')}</th>
                      <th className="p-1">{t('audit_time')}</th>
                      <th className="p-1">{t('audit_hash')}</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono">
                    {detail.hashes.map((h) => (
                      <tr key={h.seq} className="border-t border-line">
                        <td className="p-1">{h.seq}</td>
                        <td className="p-1">{h.kind}</td>
                        <td className="p-1">{h.recorded_at}</td>
                        <td className="p-1 [overflow-wrap:anywhere]">{h.entry_hash}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </section>
        <footer data-testid="mock-footer" className="text-sm text-muted">
          {t('mock_footer')}
        </footer>
      </main>
    </div>
  )
}
