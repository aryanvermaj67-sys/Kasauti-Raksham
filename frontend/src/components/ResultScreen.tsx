import { useState } from 'react'
import { logEvent, type CheckResult, type ClaimSet, type Outcome } from '../api.ts'
import { ui, verdictText, type Lang, type Params } from '../i18n.ts'

type Props = { lang: Lang; result: CheckResult; claimset: ClaimSet; onRestart: () => void }
const TONE: Record<Outcome, string> = { MATCHES: 'border-green-600', CONTRADICTS: 'border-red-600', NO_RECORD: 'border-slate-400' }
const btn = 'w-full rounded-lg border border-blue-800 px-4 py-3 text-left font-semibold text-blue-900'

function Row({ app, record, label, tone }: { app: string; record: string; label?: string; tone: string }) {
  return (
    <div className={`grid grid-cols-2 gap-3 border-l-4 bg-white p-3 [overflow-wrap:anywhere] ${tone}`}>
      <p>{app}</p>
      <div>
        <p>{record}</p>
        {label && <p className="mt-1 text-xs text-slate-600">{label}</p>}
      </div>
    </div>
  )
}

export default function ResultScreen({ lang, result, claimset, onRestart }: Props) {
  const [copied, setCopied] = useState(false)
  const [logged, setLogged] = useState<string[]>([])
  const t = (key: string, params?: Params) => ui(lang, key, params)
  const outcomes = result.verdicts.map((v) => v.outcome)
  const overall: Outcome = outcomes.includes('CONTRADICTS') ? 'CONTRADICTS' : outcomes.includes('NO_RECORD') ? 'NO_RECORD' : 'MATCHES'

  const field = (type: string, key: string) => claimset.claims.find((c) => c.type === type)?.fields[key] ?? null
  const totals = result.summary[0]?.params ?? {}
  const video = result.verdicts.find((v) => v.claim_type === 'endorsement' && v.outcome === 'CONTRADICTS')
  const complaint = [
    t('complaint', {
      ...totals,
      broker: field('broker', 'name'),
      payee: field('payee', 'upi_id') ?? field('payee', 'account_no_last4'),
      check_id: result.check_id,
      artifact_sha256: result.artifact_sha256,
    }),
    video && t('complaint_video', video.params),
    t('complaint_pack', { pack_id: `pack-${result.check_id}` }), // the reviewer exports this pack for the case
  ]
    .filter(Boolean)
    .join(' ')

  async function act(kind: 'trusted_contact' | 'bank_callback' | 'still_pay') {
    await logEvent(kind, result.check_id)
    setLogged((l) => [...l, kind])
  }

  const actionButton = (kind: 'trusted_contact' | 'bank_callback' | 'still_pay') => (
    <div key={kind}>
      <button data-testid={`act-${kind}`} className={btn} onClick={() => act(kind)}>
        {t(kind)}
      </button>
      {logged.includes(kind) && <p className="mt-1 text-sm text-slate-700">{t(kind === 'still_pay' ? 'still_pay_note' : 'event_logged')}</p>}
    </div>
  )

  return (
    <section data-testid="result" className="space-y-4">
      <h2 className="text-lg font-bold">{t('result_title')}</h2>
      <div className="grid grid-cols-2 gap-3 px-3 text-sm font-semibold text-slate-600">
        <p>{t('col_app')}</p>
        <p>{t('col_record')}</p>
      </div>
      {result.summary.map((s) => (
        <Row key={s.reason_code} {...verdictText(lang, s.reason_code, s.params)} tone="border-blue-800 font-semibold" />
      ))}
      {result.verdicts.map((v) => (
        <Row key={v.claim_id} {...verdictText(lang, v.reason_code, v.params)} label={t(`outcome_${v.outcome}`)} tone={TONE[v.outcome]} />
      ))}

      {overall === 'MATCHES' && <p className="rounded bg-green-50 p-3">{t('matches_note')}</p>}

      {overall === 'NO_RECORD' && (
        <div className="rounded bg-slate-100 p-3">
          <p className="font-semibold">{t('no_record_title')}</p>
          <p className="mt-2">{t('self_check_title')}</p>
          <ul className="ml-5 list-disc">
            <li>{t('self_check_cdsl')}</li>
            <li>{t('self_check_cas')}</li>
            <li>{t('self_check_sebi')}</li>
          </ul>
        </div>
      )}

      <div data-testid="actions" className="space-y-3">
        <h3 className="font-semibold">{t('actions_title')}</h3>
        {overall === 'CONTRADICTS' && (
          <div className="rounded-lg border bg-white p-3">
            <p className="font-semibold">{t('report_1930')}</p>
            <p className="mt-1 text-sm text-slate-600">{t('complaint_label')}</p>
            <textarea data-testid="complaint" readOnly className="mt-2 h-40 w-full rounded border p-2 text-sm" value={complaint} />
            <div className="mt-2 flex gap-2">
              <button className="rounded border px-3 py-1" onClick={() => navigator.clipboard.writeText(complaint).then(() => setCopied(true))}>
                {t(copied ? 'copied' : 'copy')}
              </button>
              <a className="rounded border px-3 py-1" href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">
                {t('open_portal')}
              </a>
            </div>
          </div>
        )}
        {overall === 'CONTRADICTS' && actionButton('trusted_contact')}
        {overall !== 'MATCHES' && actionButton('bank_callback')}
        {actionButton('still_pay')}
      </div>
      <button className="text-sm text-blue-800 underline" onClick={onRestart}>
        {t('restart')}
      </button>
    </section>
  )
}
