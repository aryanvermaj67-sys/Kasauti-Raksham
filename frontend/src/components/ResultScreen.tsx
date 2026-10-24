import { Download, Volume2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { evidencePack, logEvent, type CheckResult, type ClaimSet, type Outcome, type RecordSummary } from '../api.ts'
import { ui, verdictText, type Lang, type Params } from '../i18n.ts'
import { btn, btn2 } from '../pages/CustomerApp.tsx'
import OutcomeChip, { TONE } from './Outcome.tsx'

export const overallOf = (result: CheckResult): Outcome => {
  const outcomes = result.verdicts.map((v) => v.outcome)
  return outcomes.includes('CONTRADICTS') ? 'CONTRADICTS' : outcomes.includes('NO_RECORD') ? 'NO_RECORD' : 'MATCHES'
}

/** A voice for this language, if the computer has one installed (read-aloud stays hidden otherwise). */
function useVoice(lang: Lang) {
  const [voice, setVoice] = useState<SpeechSynthesisVoice | null>(null)
  useEffect(() => {
    if (!('speechSynthesis' in window)) return
    const find = () => setVoice(speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith(lang)) ?? null)
    find()
    speechSynthesis.addEventListener('voiceschanged', find)
    return () => speechSynthesis.removeEventListener('voiceschanged', find)
  }, [lang])
  return voice
}

function Records({ ids, records, lang }: { ids: string[]; records: RecordSummary[]; lang: Lang }) {
  const t = (key: string, params?: Params) => ui(lang, key, params)
  const used = records.filter((r) => ids.includes(r.sha256))
  return (
    <ul data-testid="verdict-records" className="mt-2 space-y-1 border-t border-line pt-2 text-xs text-muted">
      {used.map((r) => (
        <li key={r.sha256}>
          {t('record_source', { source: r.source })} · {t('record_fetched', { fetched_at: r.fetched_at })} ·{' '}
          <span className="font-semibold">{t(r.mock ? 'record_mock' : 'record_public')}</span>
        </li>
      ))}
    </ul>
  )
}

export function ResultStep({ lang, result, records, onNext }: { lang: Lang; result: CheckResult; records: RecordSummary[]; onNext: () => void }) {
  const t = (key: string, params?: Params) => ui(lang, key, params)
  const voice = useVoice(lang)
  const overall = overallOf(result)
  // read-aloud reads template text only: the same sentences the screen shows
  const spoken = [
    ...result.summary.map((s) => Object.values(verdictText(lang, s.reason_code, s.params)).join('. ')),
    ...result.verdicts.map((v) => [t(`outcome_${v.outcome}`), ...Object.values(verdictText(lang, v.reason_code, v.params))].join('. ')),
  ].join('. ')
  function speak() {
    speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(spoken)
    u.voice = voice
    u.lang = voice!.lang
    speechSynthesis.speak(u)
  }

  return (
    <section data-testid="result" className="space-y-3">
      <h2 className="text-lg font-semibold">{t('result_title')}</h2>
      {voice && (
        <button data-testid="read-aloud" className={btn2} onClick={speak}>
          <Volume2 size={16} aria-hidden /> {t('read_aloud')}
        </button>
      )}
      {result.summary.map((s) => {
        const m = verdictText(lang, s.reason_code, s.params)
        return (
          <div key={s.reason_code} className="rounded-box border-[1.5px] border-ink bg-white p-4 font-semibold">
            <p>{m.app}</p>
            <p className="mt-1">{m.record}</p>
          </div>
        )
      })}
      <div className="grid grid-cols-2 gap-3 text-xs font-bold tracking-wide text-muted">
        <p>{t('col_app')}</p>
        <p>{t('col_record')}</p>
      </div>
      {result.verdicts.map((v) => {
        const m = verdictText(lang, v.reason_code, v.params)
        return (
          <article key={v.claim_id} data-testid="verdict" data-outcome={v.outcome} className={`rounded-box border p-3 ${TONE[v.outcome].box.split(' ')[0]} bg-white`}>
            <OutcomeChip outcome={v.outcome} lang={lang} />
            <div className="mt-2 grid grid-cols-2 gap-3 text-ink [overflow-wrap:anywhere]">
              <p className="rounded-box border border-dashed border-line-2 bg-panel p-2">{m.app}</p>
              <p className="rounded-box border-[1.5px] border-ink bg-white p-2">{m.record}</p>
            </div>
            <Records ids={v.evidence_ids} records={records} lang={lang} />
          </article>
        )
      })}
      {overall === 'MATCHES' && <p className="rounded-box border border-match-line bg-match-bg p-3 text-match">{t('matches_note')}</p>}
      {overall === 'NO_RECORD' && (
        <div className="rounded-box border border-norec-line bg-panel p-3">
          <p className="font-semibold">{t('no_record_title')}</p>
          <p className="mt-2">{t('self_check_title')}</p>
          <ul className="ml-5 list-disc">
            <li>{t('self_check_cdsl')}</li>
            <li>{t('self_check_cas')}</li>
            <li>{t('self_check_sebi')}</li>
          </ul>
        </div>
      )}
      <button data-testid="next" className={btn} onClick={onNext}>
        {t('next')}
      </button>
    </section>
  )
}

type ActionProps = { lang: Lang; result: CheckResult; claimset: ClaimSet; customer: string; onNext: () => void }

export function ActionStep({ lang, result, claimset, customer, onNext }: ActionProps) {
  const [copied, setCopied] = useState(false)
  const [logged, setLogged] = useState<string[]>([])
  const t = (key: string, params?: Params) => ui(lang, key, params)
  const overall = overallOf(result)
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
    t('complaint_pack', { pack_id: `pack-${result.check_id}` }),
  ]
    .filter(Boolean)
    .join(' ')

  async function act(kind: 'trusted_contact' | 'bank_callback' | 'still_pay') {
    await logEvent(kind, result.check_id, customer)
    setLogged((l) => [...l, kind])
  }
  const actionButton = (kind: 'trusted_contact' | 'bank_callback' | 'still_pay') => (
    <div key={kind}>
      <button data-testid={`act-${kind}`} className={btn2} onClick={() => act(kind)}>
        {t(kind)}
      </button>
      {logged.includes(kind) && <p className="mt-1 text-sm">{t(kind === 'still_pay' ? 'still_pay_note' : 'event_logged')}</p>}
    </div>
  )

  return (
    <section data-testid="actions" className="space-y-3">
      <h2 className="text-lg font-semibold">{t('actions_title')}</h2>
      {overall === 'CONTRADICTS' && (
        <div className="rounded-box border border-line bg-white p-3">
          <p className="font-semibold">{t('report_1930')}</p>
          <p className="mt-1 text-sm text-muted">{t('complaint_label')}</p>
          <textarea data-testid="complaint" readOnly className="mt-2 h-44 w-full rounded-box border border-line-2 p-2 text-sm" value={complaint} />
          <div className="mt-2 grid grid-cols-2 gap-2">
            <button className={btn2} onClick={() => navigator.clipboard.writeText(complaint).then(() => setCopied(true))}>
              {t(copied ? 'copied' : 'copy')}
            </button>
            <a className={btn2} href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">
              {t('open_portal')}
            </a>
          </div>
        </div>
      )}
      {overall === 'CONTRADICTS' && actionButton('trusted_contact')}
      {overall !== 'MATCHES' && actionButton('bank_callback')}
      {actionButton('still_pay')}
      <button data-testid="next" className={btn} onClick={onNext}>
        {t('next')}
      </button>
    </section>
  )
}

export function PackStep({ lang, result, customer, onRestart }: { lang: Lang; result: CheckResult; customer: string; onRestart: () => void }) {
  const t = (key: string, params?: Params) => ui(lang, key, params)
  const [got, setGot] = useState<{ sha256: string; pack_id: string; chain_valid: boolean } | null>(null)
  const [error, setError] = useState('')

  async function download() {
    try {
      const { blob, pack, sha256 } = await evidencePack(result.check_id, customer)
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${pack.pack_id}.json`
      a.click()
      URL.revokeObjectURL(a.href)
      setGot({ sha256, pack_id: pack.pack_id, chain_valid: pack.chain_valid })
    } catch (e) {
      setError(t('error', { error: e instanceof Error ? e.message : String(e) }))
    }
  }

  return (
    <section data-testid="step-pack" className="space-y-3">
      <h2 className="text-lg font-semibold">{t('pack_title')}</h2>
      <p className="text-sm text-muted">{t('pack_note')}</p>
      <button data-testid="pack-download" className={btn} onClick={download}>
        <Download size={16} aria-hidden /> {t('pack_download')}
      </button>
      {error && <p className="text-contra">{error}</p>}
      {got && (
        <div data-testid="pack-info" className="space-y-1 rounded-box border border-line bg-white p-3 text-sm [overflow-wrap:anywhere]">
          <p className="font-semibold">{t('pack_id', { pack_id: got.pack_id })}</p>
          <p data-testid="pack-hash" className="font-mono text-xs">
            {t('pack_hash', { hash: got.sha256 })}
          </p>
          <p className={got.chain_valid ? 'text-match' : 'text-contra'}>{t(got.chain_valid ? 'pack_chain_ok' : 'pack_chain_bad')}</p>
        </div>
      )}
      <button className={btn2} onClick={onRestart}>
        {t('restart')}
      </button>
    </section>
  )
}
