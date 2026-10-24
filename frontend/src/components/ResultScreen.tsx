import { useEffect, useState } from 'react'
import { evidencePack, logEvent, type CheckResult, type ClaimSet, type Outcome, type RecordSummary } from '../api.ts'
import { ui, verdictText, type Lang, type Params } from '../i18n.ts'
import { back, btn, btn2, fwd, Icon, Kicker } from '../pages/CustomerApp.tsx'

export const overallOf = (result: CheckResult): Outcome => {
  const outcomes = result.verdicts.map((v) => v.outcome)
  return outcomes.includes('CONTRADICTS') ? 'CONTRADICTS' : outcomes.includes('NO_RECORD') ? 'NO_RECORD' : 'MATCHES'
}

// the design export's outcome boxes; MATCHES uses the spec's slate-teal (the export had no match card)
const BOX: Record<Outcome, { box: string; text: string; icon: string }> = {
  CONTRADICTS: { box: 'bg-[#ffdad6] border-[#f87171]', text: 'text-[#93000a]', icon: 'report_problem' },
  NO_RECORD: { box: 'bg-[#f2f4f6] border-[#cbd5e1]', text: 'text-[#191c1e]', icon: 'help_center' },
  MATCHES: { box: 'bg-[#f0fdfa] border-[#99f6e4]', text: 'text-[#0f766e]', icon: 'balance' },
}
const ICON_FOR: Record<string, string> = { holding: 'account_balance_wallet', broker: 'gavel', payee: 'payments', endorsement: 'smart_display', platform: 'public' }

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

type ResultProps = { lang: Lang; result: CheckResult; records: RecordSummary[]; onBack: () => void; onNext: () => void }

export function ResultStep({ lang, result, records, onBack, onNext }: ResultProps) {
  const t = (key: string, params?: Params) => ui(lang, key, params)
  const voice = useVoice(lang)
  const [speaking, setSpeaking] = useState(false)
  const overall = overallOf(result)
  // read-aloud reads template text only: the same sentences the screen shows
  const spoken = [
    ...result.summary.map((s) => Object.values(verdictText(lang, s.reason_code, s.params)).join('. ')),
    ...result.verdicts.map((v) => [t(`outcome_${v.outcome}`), ...Object.values(verdictText(lang, v.reason_code, v.params))].join('. ')),
  ].join('. ')
  function speak() {
    speechSynthesis.cancel()
    if (speaking) return setSpeaking(false)
    const u = new SpeechSynthesisUtterance(spoken)
    u.voice = voice
    u.lang = voice!.lang
    u.onend = u.onerror = () => setSpeaking(false)
    setSpeaking(true)
    speechSynthesis.speak(u)
  }
  const used = (ids: string[]) => records.filter((r) => ids.includes(r.sha256))

  return (
    <section data-testid="result" className="flex flex-col gap-3">
      {voice && (
        <div className="bg-[#f2f4f6] p-2.5 rounded-lg flex items-center justify-between shadow-2xs border border-[#e0e3e5]">
          <div className="flex items-center gap-2">
            <button data-testid="read-aloud" onClick={speak} type="button" aria-label={t(speaking ? 'stop_reading' : 'read_aloud')} className="w-8 h-8 rounded bg-[#000000] text-[#ffffff] flex items-center justify-center hover:opacity-90 active:scale-95 transition-all shadow-xs">
              <Icon name={speaking ? 'pause' : 'volume_up'} className="text-[16px]" />
            </button>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-[#191c1e]">{t('ph_audio')}</span>
              <span className="text-[10px] text-[#45464d]">{t(speaking ? 'ph_speaking' : 'ph_tap_listen')}</span>
            </div>
          </div>
        </div>
      )}

      {result.summary.map((s) => {
        const m = verdictText(lang, s.reason_code, s.params)
        return (
          <div key={s.reason_code} className="p-2.5 rounded-lg border-[1.5px] border-[#131b2e] bg-[#ffffff] flex flex-col gap-1">
            <p className="text-xs font-bold text-[#191c1e]">{m.app}</p>
            <p className="text-xs text-[#191c1e]">{m.record}</p>
          </div>
        )
      })}

      <div className="flex flex-col gap-2.5">
        {result.verdicts.map((v) => {
          const m = verdictText(lang, v.reason_code, v.params)
          const b = BOX[v.outcome]
          const recs = used(v.evidence_ids)
          return (
            <article key={v.claim_id} data-testid="verdict" data-outcome={v.outcome} className="flex flex-col rounded-lg overflow-hidden border border-[#e0e3e5] bg-[#ffffff] shadow-2xs">
              <div className="bg-[#f2f4f6] p-2.5 flex flex-col gap-1 border-b border-dashed border-[#c6c6cd]">
                <span className="text-[10px] uppercase font-bold text-[#515f74] flex items-center gap-1">
                  <Icon name="format_quote" className="text-[13px]" />
                  <span>{t('ph_claimed')}</span>
                </span>
                <p className="text-xs text-[#191c1e] [overflow-wrap:anywhere]">{m.app}</p>
              </div>
              <div className="bg-[#ffffff] p-2.5 flex flex-col gap-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] uppercase font-bold text-[#191c1e] flex items-center gap-1">
                    <Icon name={ICON_FOR[v.claim_type] ?? 'account_balance'} className="text-[14px]" />
                    <span>{t('ph_record_shows')}</span>
                  </span>
                  <span className="text-[9px] font-mono text-[#515f74] text-right [overflow-wrap:anywhere]">{recs.map((r) => r.source).join(' · ')}</span>
                </div>
                <p className="text-xs font-semibold text-[#191c1e] [overflow-wrap:anywhere]">{m.record}</p>
                <div data-testid="outcome-chip" data-outcome={v.outcome} className={`mt-1 p-1.5 rounded border flex items-center gap-1.5 ${b.box}`}>
                  <Icon name={b.icon} className={`text-[16px] ${b.text}`} />
                  <div className="flex flex-col">
                    <span className={`text-[10px] uppercase font-bold ${b.text}`}>{t(`outcome_${v.outcome}`)}</span>
                    <span data-testid="verdict-records" className={`text-[9px] ${b.text} [overflow-wrap:anywhere]`}>
                      {recs.map((r) => `${t('record_fetched', { fetched_at: r.fetched_at })} · ${t(r.mock ? 'record_mock' : 'record_public')}`).join(' | ')}
                    </span>
                  </div>
                </div>
              </div>
            </article>
          )
        })}
      </div>

      {overall === 'MATCHES' && <p className="p-2.5 rounded-lg bg-[#f0fdfa] border border-[#99f6e4] text-[#0f766e] text-xs">{t('matches_note')}</p>}
      {overall === 'NO_RECORD' && (
        <div className="p-2.5 rounded-lg bg-[#f2f4f6] border border-[#cbd5e1] text-[#191c1e] text-xs flex flex-col gap-1">
          <p className="font-bold">{t('no_record_title')}</p>
          <p>{t('self_check_title')}</p>
          <ul className="ml-4 list-disc">
            <li>{t('self_check_cdsl')}</li>
            <li>{t('self_check_cas')}</li>
            <li>{t('self_check_sebi')}</li>
          </ul>
        </div>
      )}

      <div className="mt-auto flex justify-between items-center pt-3 border-t border-[#f2f4f6]">
        <button onClick={onBack} type="button" className={back}>
          {t('back')}
        </button>
        <button data-testid="next" onClick={onNext} type="button" className={fwd}>
          <span>{t('ph_next_steps')}</span>
          <Icon name="arrow_forward" className="text-[14px]" />
        </button>
      </div>
    </section>
  )
}

type ActionProps = { lang: Lang; result: CheckResult; claimset: ClaimSet; customer: string; onNext: () => void }
const row = 'p-3 rounded-lg text-left flex items-start gap-2.5 border transition-all w-full'

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
  const note = (kind: string, fallback: string) => (logged.includes(kind) ? t(kind === 'still_pay' ? 'still_pay_note' : 'event_logged') : t(fallback))

  return (
    <section data-testid="actions" className="flex flex-col gap-3">
      <Kicker kicker={t('ph_kicker_7')} title={t('ph_safeguards')} desc={t('ph_safeguards_desc')} />
      <div className="flex flex-col gap-2">
        {overall === 'CONTRADICTS' && (
          <div className="p-3 bg-[#eceef0] rounded-lg flex flex-col gap-2 shadow-2xs border border-[#c6c6cd]">
            <div className="flex items-start gap-2.5">
              <Icon name="flag" className="text-[#ba1a1a] text-[22px] mt-0.5" />
              <div className="flex flex-col flex-1">
                <span className="text-xs font-bold text-[#191c1e]">{t('ph_cyber')}</span>
                <span className="text-[10px] text-[#45464d] mt-0.5">{t('ph_cyber_desc')}</span>
              </div>
            </div>
            <textarea data-testid="complaint" readOnly aria-label={t('complaint_label')} className="h-36 w-full rounded border border-[#c6c6cd] bg-[#ffffff] p-2 text-[11px] text-[#191c1e]" value={complaint} />
            <div className="grid grid-cols-2 gap-2">
              <button type="button" className={btn2} onClick={() => navigator.clipboard.writeText(complaint).then(() => setCopied(true))}>
                {t(copied ? 'copied' : 'copy')}
              </button>
              <a className={btn2} href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">
                {t('open_portal')}
              </a>
            </div>
          </div>
        )}
        {overall === 'CONTRADICTS' && (
          <button data-testid="act-trusted_contact" onClick={() => act('trusted_contact')} type="button" className={`${row} bg-[#f2f4f6] hover:bg-[#eceef0] border-[#e0e3e5]`}>
            <Icon name="contact_phone" className="text-[#515f74] text-[22px] mt-0.5" />
            <div className="flex flex-col flex-1">
              <span className="text-xs font-bold text-[#191c1e]">{t('ph_family')}</span>
              <span className="text-[10px] text-[#45464d]">{note('trusted_contact', 'ph_family_desc')}</span>
            </div>
            <Icon name="call" className="text-[16px] text-[#515f74]" />
          </button>
        )}
        {overall !== 'MATCHES' && (
          <button data-testid="act-bank_callback" onClick={() => act('bank_callback')} type="button" className={`${row} bg-[#f2f4f6] hover:bg-[#eceef0] border-[#e0e3e5]`}>
            <Icon name="support_agent" className="text-[#515f74] text-[22px] mt-0.5" />
            <div className="flex flex-col flex-1">
              <span className="text-xs font-bold text-[#191c1e]">{t('ph_callback')}</span>
              <span className="text-[10px] text-[#45464d]">{note('bank_callback', 'ph_callback_desc')}</span>
            </div>
            <Icon name="chevron_right" className="text-[16px] text-[#515f74]" />
          </button>
        )}
      </div>
      <div className="pt-2 flex flex-col items-center gap-2 border-t border-[#f2f4f6]">
        <button data-testid="next" onClick={onNext} type="button" className={btn}>
          <Icon name="inventory_2" className="text-[16px]" />
          <span>{t('ph_view_pack')}</span>
        </button>
        <button data-testid="act-still_pay" onClick={() => act('still_pay')} type="button" className="py-1 text-[#515f74] hover:text-[#191c1e] text-[11px] underline text-center">
          {t('ph_continue_anyway')}
        </button>
        {logged.includes('still_pay') && <p className="text-[11px] text-[#191c1e]">{t('still_pay_note')}</p>}
      </div>
    </section>
  )
}

export function PackStep({ lang, result, customer, onRestart }: { lang: Lang; result: CheckResult; customer: string; onRestart: () => void }) {
  const t = (key: string, params?: Params) => ui(lang, key, params)
  const [got, setGot] = useState<{ sha256: string; pack_id: string; chain_valid: boolean; exported_at: string } | null>(null)
  const [error, setError] = useState('')

  async function download() {
    try {
      const { blob, pack, sha256 } = await evidencePack(result.check_id, customer)
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${pack.pack_id}.json`
      a.click()
      URL.revokeObjectURL(a.href)
      setGot({ sha256, pack_id: pack.pack_id, chain_valid: pack.chain_valid, exported_at: (pack as { exported_at?: string }).exported_at ?? '' })
    } catch (e) {
      setError(t('error', { error: e instanceof Error ? e.message : String(e) }))
    }
  }

  return (
    <section data-testid="step-pack" className="flex flex-col gap-3">
      <Kicker kicker={t('ph_kicker_8')} title={t('ph_pack')} desc={t('ph_pack_desc')} />
      <div className="bg-[#f2f4f6] p-3 rounded-lg flex flex-col gap-2 font-mono text-[11px] text-[#45464d] border border-[#e0e3e5]">
        <div className="flex flex-col gap-0.5">
          <span className="uppercase text-[9px]">{t('ph_pack_artifact')}</span>
          <span className="break-all text-[#191c1e] font-mono text-[9px] bg-[#ffffff] p-1 rounded border border-[#e0e3e5]">{result.artifact_sha256}</span>
        </div>
        {got && (
          <div data-testid="pack-info" className="flex flex-col gap-2">
            <div className="flex justify-between border-b border-[#e0e3e5] pb-1 gap-2">
              <span className="uppercase text-[10px]">{t('ph_pack_id')}</span>
              <span className="text-[#191c1e] font-bold [overflow-wrap:anywhere]">{got.pack_id}</span>
            </div>
            <div className="flex justify-between border-b border-[#e0e3e5] pb-1 gap-2">
              <span className="uppercase text-[10px]">{t('ph_pack_generated')}</span>
              <span className="text-[#191c1e] text-[10px]">{got.exported_at}</span>
            </div>
            <div data-testid="pack-hash" className="flex flex-col gap-0.5">
              <span className="uppercase text-[9px]">{t('ph_pack_sha')}</span>
              <span className="break-all text-[#191c1e] font-mono text-[9px] bg-[#ffffff] p-1 rounded border border-[#e0e3e5]">{got.sha256}</span>
            </div>
            <div className="flex items-center gap-1.5 pt-1 text-[#191c1e]">
              <Icon name={got.chain_valid ? 'link' : 'link_off'} className="text-[#515f74] text-[15px]" />
              <span className="text-xs font-bold">{t(got.chain_valid ? 'pack_chain_ok' : 'pack_chain_bad')}</span>
            </div>
          </div>
        )}
        <span className="font-sans text-[10px]">{t('pack_note')}</span>
      </div>
      {error && <p className="text-[11px] text-[#93000a]">{error}</p>}
      <div className="flex flex-col gap-2 pt-2 border-t border-[#f2f4f6]">
        <button data-testid="pack-download" onClick={download} type="button" className={btn}>
          <Icon name="download" className="text-[16px]" />
          <span>{t('ph_pack_download')}</span>
        </button>
        <button onClick={onRestart} type="button" className={btn2}>
          {t('ph_start_new')}
        </button>
      </div>
    </section>
  )
}
