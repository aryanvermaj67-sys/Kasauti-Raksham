import { useEffect, useState } from 'react'
import {
  ackPrompt,
  checkRecords,
  demoFile,
  isinCandidates,
  readArtifact,
  runCheck,
  scenarios,
  triggerPrompts,
  uploadVideo,
  URL_CUSTOMER,
  type Candidate,
  type CheckResult,
  type Claim,
  type ClaimSet,
  type FieldValue,
  type Prompt,
  type RecordSummary,
  type Scenario,
} from '../api.ts'
import Header, { useHealth, useLarge } from '../components/Header.tsx'
import { ActionStep, PackStep, ResultStep } from '../components/ResultScreen.tsx'
import { ui, type Lang, type Params } from '../i18n.ts'

export const STEPS = ['payment', 'upload', 'confirm', 'consent', 'checking', 'result', 'action', 'pack'] as const
type Step = (typeof STEPS)[number]
type Stage = 'waiting' | 'running' | 'done'

const HIDDEN_FIELDS = ['media_sha256']
const NUMBER_FIELDS = ['quantity', 'value_inr']
// the claim schema's formats (backend/app/schemas/claims.py): a wrong one is stopped here, not by a server error
const FIELD_PATTERN: Record<string, RegExp> = { account_no_last4: /^[0-9]{4}$/, ifsc: /^[A-Z]{4}0[A-Z0-9]{6}$/ }
const badFormat = (k: string, v: unknown) => v !== null && v !== '' && k in FIELD_PATTERN && !FIELD_PATTERN[k].test(String(v))
const BOOL_FIELDS = ['claims_registered', 'claims_licensed']
const SELECT_FIELDS: Record<string, string[]> = { described_as: ['broker', 'advisor', 'other'], category: ['equity', 'forex', 'crypto', 'other'] }
// empty claims the customer can add (field names from docs/formats/claims.schema.json; endorsements need a video)
const BLANK: Record<string, Record<string, FieldValue>> = {
  holding: { instrument_name: null, isin: null, quantity: null, value_inr: null },
  broker: { name: null, sebi_reg_no: null, claims_registered: false },
  payee: { upi_id: null, account_no_last4: null, ifsc: null, described_as: 'other' },
  platform: { name: null, category: 'other', claims_licensed: false },
}
const MOCK_OTP = '123456'
const params = new URLSearchParams(window.location.search) // ?scenario= and ?lang= come from /present

// classes from the design export (ui_incoming/src/components/CustomerPhone.tsx)
export const btn = 'w-full py-2.5 bg-[#000000] text-[#ffffff] rounded font-semibold text-xs flex items-center justify-center gap-1.5 shadow-sm hover:bg-[#131b2e] transition-all disabled:bg-[#e0e3e5] disabled:text-[#76777d] disabled:cursor-not-allowed'
export const btn2 = 'w-full py-2 bg-[#eceef0] text-[#191c1e] text-xs font-semibold rounded hover:bg-[#e0e3e5] border border-[#c6c6cd] text-center'
export const back = 'py-2 px-3.5 bg-[#eceef0] text-[#191c1e] text-xs font-semibold rounded hover:bg-[#e0e3e5]'
export const fwd = 'py-2 px-4 bg-[#000000] text-[#ffffff] text-xs font-semibold rounded flex items-center gap-1 shadow-sm disabled:bg-[#e0e3e5] disabled:text-[#76777d]'
export const panel = 'bg-[#f2f4f6] p-3 rounded-lg flex flex-col gap-2 border border-[#e0e3e5]'
const input = 'w-full px-2 py-1 bg-[#ffffff] text-[#191c1e] text-xs rounded border border-[#c6c6cd] focus:outline-none focus:border-[#000000]'
const tile = 'flex-1 py-3.5 bg-[#eceef0] hover:bg-[#e0e3e5] rounded-lg flex flex-col items-center justify-center gap-1 text-[#191c1e] border border-[#c6c6cd] transition-all cursor-pointer'
const JUMP_ON = 'bg-[#000000] text-[#ffffff] font-bold shadow-xs'
const JUMP_OFF = 'bg-[#ffffff] text-[#191c1e] hover:bg-[#d8dadc] disabled:opacity-40'
const SCENARIO_ON = 'bg-[#ffffff] border-[#000000]'
const SCENARIO_OFF = 'bg-[#f2f4f6] hover:bg-[#eceef0] border-[#e0e3e5]'

export const Icon = ({ name, className = '' }: { name: string; className?: string }) => (
  <span className={`material-symbols-outlined ${className}`} aria-hidden>
    {name}
  </span>
)

export function Kicker({ kicker, title, desc }: { kicker?: string; title: string; desc?: string }) {
  return (
    <div className="flex flex-col">
      {kicker && <span className="text-xs text-[#515f74] uppercase font-semibold">{kicker}</span>}
      <h2 className="font-bold text-base text-[#191c1e]">{title}</h2>
      {desc && <p className="text-xs text-[#45464d] mt-0.5">{desc}</p>}
    </div>
  )
}

const DONE_CHIP = 'bg-[#ffffff] text-[#191c1e] border border-[#e0e3e5]'
const WAIT_CHIP = 'bg-[#eceef0] text-[#515f74]'

export function StageRow({ title, sub, stage, lang, icon = 'database' }: { title: string; sub?: string; stage: Stage; lang: Lang; icon?: string }) {
  const done = stage === 'done'
  return (
    <li data-testid="stage" data-stage={stage} className="p-2.5 bg-[#f2f4f6] rounded-lg flex items-center justify-between gap-2 border border-[#e0e3e5]">
      <div className="flex items-center gap-2 min-w-0">
        <Icon name={done ? icon : 'progress_activity'} className={`text-[18px] ${done ? 'text-[#191c1e]' : 'text-[#515f74] animate-spin'}`} />
        <div className="flex flex-col min-w-0">
          <span className="text-xs font-semibold text-[#191c1e] [overflow-wrap:anywhere]">{title}</span>
          {sub && <span className="text-[10px] text-[#45464d] [overflow-wrap:anywhere]">{sub}</span>}
        </div>
      </div>
      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase whitespace-nowrap ${done ? DONE_CHIP : WAIT_CHIP}`}>{ui(lang, `progress_${stage}`)}</span>
    </li>
  )
}

export default function CustomerApp() {
  const [lang, setLang] = useState<Lang>(params.get('lang') === 'hi' ? 'hi' : 'en')
  const [large, setLarge] = useLarge()
  const status = useHealth()
  const [step, setStep] = useState<Step>('payment')
  const [reached, setReached] = useState(0)
  const [list, setList] = useState<Scenario[]>([])
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [customer, setCustomer] = useState(URL_CUSTOMER ?? '')
  const [payee, setPayee] = useState('')
  const [amount, setAmount] = useState('')
  const [skipped, setSkipped] = useState(false)
  const [shot, setShot] = useState<File | null>(null)
  const [video, setVideo] = useState<File | null>(null)
  const [claimset, setClaimset] = useState<ClaimSet | null>(null)
  const [choices, setChoices] = useState<Record<string, Candidate[]>>({})
  const [picked, setPicked] = useState<Record<string, string>>({})
  const [adding, setAdding] = useState(false)
  const [addType, setAddType] = useState('holding')
  const [otp, setOtp] = useState('')
  const [otpWrong, setOtpWrong] = useState(false)
  const [stages, setStages] = useState<Record<string, Stage>>({})
  const [result, setResult] = useState<CheckResult | null>(null)
  const [records, setRecords] = useState<RecordSummary[]>([])
  const [error, setError] = useState('')
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [clock, setClock] = useState(() => new Date())
  const t = (key: string, p?: Params) => ui(lang, key, p)
  const fail = (e: unknown) => {
    const msg = e instanceof Error ? e.message : String(e)
    const bad = msg.match(/"fields","(\w+)"\]/) // a 422 names the field: say which, not the raw JSON
    setError(bad ? t('error_field', { field: t(`field_${bad[1]}`) }) : t('error', { error: msg }))
  }
  const stage = (k: string, s: Stage) => setStages((x) => ({ ...x, [k]: s }))
  const go = (s: Step) => {
    setStep(s)
    setReached((r) => Math.max(r, STEPS.indexOf(s)))
  }

  useEffect(() => {
    scenarios()
      .then((s) => {
        setList(s)
        const wanted = s.find((x) => x.id === params.get('scenario'))
        if (wanted || (!URL_CUSTOMER && s[0])) choose(wanted ?? s[0])
      })
      .catch(fail)
    const timer = setInterval(() => setClock(new Date()), 30000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  useEffect(() => {
    if (customer) triggerPrompts(customer).then(setPrompts).catch(() => setPrompts([])) // a failed trigger never blocks the app
  }, [customer])

  function choose(s: Scenario) {
    setScenario(s)
    setCustomer(s.customer_id)
    setPayee(s.payment_request?.payee ?? '')
  }

  async function loadScenario(s: Scenario) {
    choose(s)
    setShot(await demoFile(s.screenshot))
    setVideo(s.video ? await demoFile(s.video) : null)
  }

  async function resolveIsin(claim: Claim) {
    const name = String(claim.fields.instrument_name ?? '')
    const found = name ? await isinCandidates(name) : []
    setChoices(({ [claim.id]: _old, ...rest }) => (void _old, found.length > 1 ? { ...rest, [claim.id]: found } : rest))
    setPicked(({ [claim.id]: _old, ...rest }) => (void _old, rest))
    setField(claim.id, 'isin', found.length === 1 ? found[0].isin : null)
  }

  async function read() {
    if (!shot) return
    setError('')
    setStages({ read: 'running', ...(video ? { video: 'waiting' } : {}) })
    try {
      const cs = await readArtifact(shot)
      stage('read', 'done')
      if (video) {
        stage('video', 'running')
        const { media_sha256, match } = await uploadVideo(video)
        // the words changed from the source are the claim; with no change or no source, the opening words
        const quote = match.quote || match.transcript.split(' ').slice(0, 25).join(' ')
        cs.claims.push({ id: `c${cs.claims.length + 1}`, type: 'endorsement', fields: { person: '', quote, media_sha256 } })
        stage('video', 'done')
      }
      setClaimset(cs)
      setChoices({})
      setPicked({})
      go('confirm')
      await Promise.all(cs.claims.filter((c) => c.type === 'holding' && c.fields.isin === null).map(resolveIsin))
    } catch (e) {
      fail(e)
      setStages({})
    }
  }

  function setField(id: string, key: string, value: FieldValue) {
    setClaimset((cs) => cs && { ...cs, claims: cs.claims.map((c) => (c.id === id ? { ...c, fields: { ...c.fields, [key]: value } } : c)) })
  }
  const removeClaim = (id: string) => setClaimset((cs) => cs && { ...cs, claims: cs.claims.filter((c) => c.id !== id) })
  function addClaim() {
    setClaimset((cs) => {
      if (!cs) return cs
      const n = Math.max(0, ...cs.claims.map((c) => Number(c.id.slice(1)) || 0)) + 1
      return { ...cs, claims: [...cs.claims, { id: `c${n}`, type: addType as Claim['type'], fields: { ...BLANK[addType] } }] }
    })
    setAdding(false)
  }
  function pick(id: string, isin: string) {
    setPicked((p) => ({ ...p, [id]: isin }))
    setField(id, 'isin', isin || null) // '' means the customer skipped the choice: the check returns HOLDING_NAME_AMBIGUOUS
  }

  async function check(scope: string[]) {
    if (scope.length && otp !== MOCK_OTP) return setOtpWrong(true)
    setOtpWrong(false)
    setError('')
    go('checking')
    setStages({ check: 'running', records: 'waiting' })
    try {
      const r = await runCheck(claimset!, customer, `consent-mock-${crypto.randomUUID().slice(0, 8)}`, scope)
      setResult(r)
      stage('check', 'done')
      stage('records', 'running')
      setRecords(await checkRecords(r.check_id, customer))
      stage('records', 'done')
    } catch (e) {
      fail(e)
      setStep('consent')
    }
  }

  function restart() {
    setStep('payment')
    setReached(0)
    setShot(null)
    setVideo(null)
    setClaimset(null)
    setResult(null)
    setRecords([])
    setStages({})
    setOtp('')
    setSkipped(false)
    setError('')
    if (scenario) choose(scenario)
  }

  const allPicked = Object.keys(choices).every((id) => id in picked)
  const idx = STEPS.indexOf(step)
  const percent = (((idx + 1) / STEPS.length) * 100).toFixed(1)

  return (
    <div lang={lang} className="min-h-screen bg-[#f7f9fb]">
      <Header lang={lang} setLang={setLang} large={large} setLarge={setLarge} status={status} onReset={restart} />
      <div className="w-full flex flex-col items-center justify-start py-6 px-3 sm:px-6">
        <div
          data-testid="phone"
          style={{ zoom: large ? 1.1875 : 1 }} // large-text mode: the design's 16 px base becomes 19 px
          className="w-full max-w-[430px] bg-[#ffffff] rounded-2xl shadow-xl flex flex-col relative overflow-hidden border border-[#c6c6cd]"
        >
          {/* status bar */}
          <div className="w-full bg-[#131b2e] px-4 pt-2.5 pb-1 flex items-center justify-between text-[#ffffff] text-xs font-mono select-none">
            <span className="font-bold tracking-tight">{clock.toTimeString().slice(0, 5)}</span>
            <div className="w-20 h-3.5 bg-[#000000] rounded-full mx-auto -mt-1 opacity-90" />
            <div className="flex items-center gap-1.5 text-[12px]">
              <Icon name="signal_cellular_4_bar" className="text-[13px]" />
              <Icon name="wifi" className="text-[13px]" />
              <Icon name="battery_charging_full" className="text-[13px]" />
            </div>
          </div>

          {/* brand bar */}
          <div className="bg-[#131b2e] text-[#ffffff] px-4 py-2.5 flex items-center justify-between border-b border-[#3f465c]">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded bg-[#ffffff] text-[#000000] font-bold text-xs flex items-center justify-center shadow-xs">K</span>
              <div className="flex flex-col">
                <div className="flex items-center gap-1">
                  <span className="text-xs uppercase font-bold text-[#ffffff] tracking-tight">{t('ph_brand')}</span>
                  <span className="text-[10px] text-[#bec6e0] font-normal opacity-80">{t('ph_bank')}</span>
                </div>
                <span className="text-[9px] text-[#bec6e0] font-mono tracking-wide">{t('ph_subtitle')}</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button data-testid="lang-toggle" onClick={() => setLang(lang === 'en' ? 'hi' : 'en')} type="button" className="px-2 py-0.5 rounded bg-[#ffffff]/20 text-[#ffffff] text-[11px] font-semibold hover:bg-[#ffffff]/30 transition-colors">
                {t('ph_lang')}
              </button>
              <button onClick={restart} type="button" aria-label={t('reset')} className="p-1 rounded bg-[#ffffff]/20 text-[#ffffff] hover:bg-[#ffffff]/30 transition-colors flex items-center">
                <Icon name="restart_alt" className="text-[14px]" />
              </button>
            </div>
          </div>

          {/* quick jump: only to steps already reached, so every screen has real data behind it */}
          <div className="w-full bg-[#eceef0] px-2 py-1 flex items-center justify-between overflow-x-auto text-[11px] font-semibold gap-1 border-b border-[#e0e3e5]">
            {STEPS.map((s, i) => (
              <button key={s} type="button" data-testid={`jump-${s}`} disabled={i > reached} onClick={() => setStep(s)} className={`px-2 py-0.5 rounded text-[10px] whitespace-nowrap ${step === s ? JUMP_ON : JUMP_OFF}`}>
                {t(`ph_jump_${i + 1}`)}
              </button>
            ))}
          </div>

          {/* stepper */}
          <div className="bg-[#f2f4f6] px-4 py-2 flex flex-col gap-1.5 border-b border-[#e0e3e5]">
            <div className="flex items-center justify-between text-[#45464d] text-xs">
              <span data-testid="step-title" className="uppercase tracking-wider font-semibold text-[11px]">
                {t(`ph_title_${idx + 1}`)}
              </span>
              <span className="font-mono text-[11px] font-bold text-[#191c1e]">{percent}%</span>
            </div>
            <div className="w-full bg-[#e0e3e5] h-1.5 rounded-full overflow-hidden flex">
              <div className="bg-[#000000] h-full transition-all duration-300" style={{ width: `${percent}%` }} />
            </div>
          </div>

          <div className="p-4 min-h-[560px] flex flex-col justify-between">
            {error && <p className="mb-3 p-2 rounded bg-[#ffdad6] border border-[#f87171] text-[#93000a] text-xs [overflow-wrap:anywhere]">{error}</p>}

            {step === 'payment' && (
              <section data-testid="step-payment" className="flex flex-col gap-3.5">
                <div className="flex items-center gap-1.5 text-[#191c1e]">
                  <Icon name="send_money" className="text-[#515f74]" />
                  <h2 className="font-bold text-base">{t('ph_transfer')}</h2>
                </div>
                {prompts[0] && (
                  <div data-testid="trigger-banner" className="p-2.5 rounded-lg bg-[#ffdad6] border border-[#f87171] text-[#93000a] flex flex-col gap-1">
                    <span className="text-xs font-bold">{t('trigger_title')}</span>
                    <span className="text-[11px] [overflow-wrap:anywhere]">{t(`trigger_${prompts[0].reason}`, { payee: prompts[0].payee })}</span>
                    <span className="text-[10px]">{t('trigger_not_blocked')}</span>
                    <button data-testid="trigger-dismiss" type="button" className={`${btn2} mt-1`} onClick={() => ackPrompt(customer, prompts[0].campaign).then(() => setPrompts((p) => p.slice(1)))}>
                      {t('trigger_dismiss')}
                    </button>
                  </div>
                )}
                <div className="bg-[#f2f4f6] p-3.5 rounded-lg flex flex-col gap-2 border border-[#e0e3e5]">
                  <label className="flex justify-between items-baseline gap-3">
                    <span className="text-xs text-[#45464d] whitespace-nowrap">{t('ph_beneficiary')}</span>
                    <input data-testid="payment-payee" value={payee} onChange={(e) => setPayee(e.target.value)} className="min-w-0 flex-1 text-right text-xs font-bold text-[#191c1e] bg-transparent focus:outline-none focus:bg-[#ffffff] rounded px-1" />
                  </label>
                  {scenario?.payment_request && <span className="text-[10px] text-[#45464d] text-right">{t('payment_prefilled')}</span>}
                  <label className="pt-2 border-t border-[#e0e3e5] flex justify-between items-baseline gap-3">
                    <span className="text-xs text-[#45464d] whitespace-nowrap">
                      {t('ph_amount')} <span className="text-[10px]">({t('ph_amount_hint')})</span>
                    </span>
                    <input data-testid="payment-amount" inputMode="numeric" value={amount} onChange={(e) => setAmount(e.target.value)} className="min-w-0 w-32 text-right text-xl text-[#000000] font-bold tabular-nums bg-[#ffffff] border border-[#e0e3e5] rounded px-1" />
                  </label>
                </div>

                <div className="bg-[#eceef0] p-3.5 rounded-lg flex flex-col gap-2.5 shadow-xs border border-[#c6c6cd]">
                  <div className="flex items-start gap-2">
                    <Icon name="policy" className="text-[#515f74] text-[20px] mt-0.5" />
                    <div className="flex flex-col">
                      <span className="text-xs font-bold text-[#191c1e]">{t('ph_check_before')}</span>
                      <p className="text-[11px] text-[#45464d] mt-0.5 leading-snug">{t('ph_check_before_desc')}</p>
                    </div>
                  </div>
                  {status !== 'ready' && (
                    <p data-testid="preparing" className="text-[11px] text-[#45464d] flex items-center gap-1">
                      <Icon name="progress_activity" className="text-[14px] animate-spin" /> {t('preparing')}
                    </p>
                  )}
                  <div className="flex flex-col gap-2 pt-1">
                    <button data-testid="check-button" onClick={() => go('upload')} disabled={status !== 'ready' || !customer} type="button" className={btn}>
                      <Icon name="policy" className="text-[16px]" />
                      <span>{t('ph_verify')}</span>
                    </button>
                    <button data-testid="pay-skip" onClick={() => setSkipped(true)} type="button" className="w-full py-1.5 bg-transparent text-[#515f74] text-[11px] hover:text-[#191c1e] text-center">
                      {t('ph_not_now')}
                    </button>
                    {skipped && <p className="text-[11px] text-[#191c1e] text-center">{t('still_pay_note')}</p>}
                  </div>
                </div>

                <div className="bg-[#f2f4f6] p-2 rounded text-[#45464d] flex items-center gap-1.5 border border-[#e0e3e5]">
                  <Icon name="gavel" className="text-[15px] text-[#515f74]" />
                  <span className="text-[11px] leading-tight">{t('ph_disclaimer')}</span>
                </div>
              </section>
            )}

            {step === 'upload' && (
              <section data-testid="step-upload" className="flex flex-col gap-3.5">
                <Kicker kicker={t('ph_kicker_2')} title={t('ph_share')} desc={t('ph_share_desc')} />
                <div className="flex gap-2">
                  <label className={tile}>
                    <Icon name="photo_camera" className="text-[24px]" />
                    <span className="text-xs font-semibold">{t('ph_camera')}</span>
                    <input type="file" accept="image/*" capture="environment" className="sr-only" onChange={(e) => setShot(e.target.files?.[0] ?? null)} />
                  </label>
                  <label className={tile}>
                    <Icon name="upload_file" className="text-[24px]" />
                    <span className="text-xs font-semibold">{t('ph_gallery')}</span>
                    <input data-testid="shot-input" type="file" accept="image/png,image/jpeg" className="sr-only" onChange={(e) => setShot(e.target.files?.[0] ?? null)} />
                  </label>
                  <label className={tile}>
                    <Icon name="videocam" className="text-[24px]" />
                    <span className="text-xs font-semibold">{t('ph_video')}</span>
                    <input data-testid="video-input" type="file" accept="video/mp4" className="sr-only" onChange={(e) => setVideo(e.target.files?.[0] ?? null)} />
                  </label>
                </div>
                {(shot || video) && (
                  <p data-testid="selected-files" className="text-[11px] text-[#191c1e] [overflow-wrap:anywhere]">
                    {t('ph_selected', { files: [shot?.name, video?.name].filter(Boolean) })}
                  </p>
                )}
                {video && <p className="text-[10px] text-[#45464d]">{t('video_note')}</p>}

                {list.length > 0 && (
                  <div className="flex flex-col gap-1.5">
                    <span className="text-[11px] text-[#45464d] uppercase font-semibold">{t('ph_or_scenario')}</span>
                    {list.map((s, i) => (
                      <button
                        key={s.id}
                        data-testid={`use-${s.id}`}
                        type="button"
                        onClick={() => loadScenario(s).catch(fail)}
                        className={`p-2.5 rounded-lg text-left flex items-start gap-2 border transition-all ${scenario?.id === s.id && shot ? SCENARIO_ON : SCENARIO_OFF}`}
                      >
                        <Icon name={s.video ? 'videocam' : 'account_balance_wallet'} className="text-[#515f74] text-[18px] mt-0.5" />
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-[#191c1e]">
                            {i + 1}. {s.id}
                          </span>
                          <span className="text-[10px] text-[#45464d]">{t(s.video ? 'ph_scenario_video' : 'ph_scenario_desc', { customer: s.customer_id })}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {Object.keys(stages).length > 0 && (
                  <ul className="flex flex-col gap-2">
                    {stages.read && <StageRow title={t('progress_read')} stage={stages.read} lang={lang} icon="document_scanner" />}
                    {stages.video && <StageRow title={t('progress_video')} stage={stages.video} lang={lang} icon="smart_display" />}
                  </ul>
                )}

                <div className="mt-auto flex justify-between items-center pt-3 border-t border-[#f2f4f6]">
                  <button onClick={() => setStep('payment')} type="button" className={back}>
                    {t('back')}
                  </button>
                  <button data-testid="read-button" onClick={read} disabled={!shot || stages.read === 'running'} type="button" className={fwd}>
                    <span>{t('ph_analyze')}</span>
                    <Icon name="arrow_forward" className="text-[14px]" />
                  </button>
                </div>
              </section>
            )}

            {step === 'confirm' && claimset && (
              <section data-testid="confirm" className="flex flex-col gap-3">
                <Kicker kicker={t('ph_kicker_3')} title={t('ph_extracted')} desc={t('ph_extracted_desc')} />
                <div className="flex flex-col gap-2">
                  {claimset.claims.map((c) => (
                    <fieldset key={c.id} data-testid={`claim-${c.id}`} className="p-2.5 bg-[#f2f4f6] rounded-lg flex flex-col gap-1.5 border border-[#e0e3e5]">
                      <div className="flex items-center justify-between">
                        <legend className="text-[11px] font-bold uppercase text-[#515f74]">{t(`claim_${c.type}`)}</legend>
                        <button data-testid={`remove-${c.id}`} onClick={() => removeClaim(c.id)} type="button" aria-label={t('remove_claim')} className="text-[#ba1a1a] hover:opacity-80 p-0.5">
                          <Icon name="delete" className="text-[16px]" />
                        </button>
                      </div>
                      {Object.entries(c.fields)
                        .filter(([k]) => !HIDDEN_FIELDS.includes(k))
                        .map(([k, v]) => (
                          <label key={k} className="flex flex-col gap-0.5">
                            <span className="text-[10px] text-[#45464d]">{t(`field_${k}`)}</span>
                            {BOOL_FIELDS.includes(k) ? (
                              <input type="checkbox" className="size-[18px] accent-[#000000]" checked={Boolean(v)} onChange={(e) => setField(c.id, k, e.target.checked)} />
                            ) : SELECT_FIELDS[k] ? (
                              <select className={input} value={String(v)} onChange={(e) => setField(c.id, k, e.target.value)}>
                                {SELECT_FIELDS[k].map((o) => (
                                  <option key={o}>{o}</option>
                                ))}
                              </select>
                            ) : (
                              <input
                                className={input}
                                readOnly={k === 'isin'}
                                data-testid={`field-${c.type}-${k}`}
                                type={NUMBER_FIELDS.includes(k) ? 'number' : 'text'}
                                value={v === null ? '' : String(v)}
                                onChange={(e) => setField(c.id, k, NUMBER_FIELDS.includes(k) ? (e.target.value === '' ? null : Number(e.target.value)) : (k === 'ifsc' ? e.target.value.toUpperCase() : e.target.value) || null)}
                                onBlur={k === 'instrument_name' ? () => resolveIsin(c).catch(fail) : undefined}
                              />
                            )}
                            {badFormat(k, v) && (
                              <span data-testid={`bad-${c.type}-${k}`} className="text-[10px] text-[#ba1a1a]">
                                {t(`hint_${k}`)}
                              </span>
                            )}
                          </label>
                        ))}
                      {choices[c.id] && (
                        <div data-testid={`choices-${c.id}`} className="mt-1 p-2 rounded bg-[#ffffff] border border-[#c6c6cd] flex flex-col gap-1">
                          <p className="text-[11px] text-[#191c1e]">{t('ambiguous_pick')}</p>
                          {[...choices[c.id], { isin: '', name: t('skip_choice') }].map((o) => (
                            <label key={o.isin || 'skip'} className="flex items-center gap-2 text-[11px] text-[#191c1e]">
                              <input type="radio" name={`pick-${c.id}`} checked={picked[c.id] === o.isin} onChange={() => pick(c.id, o.isin)} />
                              {o.isin ? `${o.isin} · ${o.name}` : o.name}
                            </label>
                          ))}
                        </div>
                      )}
                    </fieldset>
                  ))}
                </div>
                {adding ? (
                  <div className="flex gap-1.5 mt-1">
                    <select data-testid="add-type" value={addType} onChange={(e) => setAddType(e.target.value)} className="flex-1 px-2.5 py-1 text-xs bg-[#ffffff] border border-[#c6c6cd] rounded text-[#191c1e] focus:outline-none focus:border-[#000000]">
                      {Object.keys(BLANK).map((type) => (
                        <option key={type} value={type}>
                          {t(`claim_${type}`)}
                        </option>
                      ))}
                    </select>
                    <button data-testid="add-save" type="button" onClick={addClaim} className="px-3 py-1 bg-[#000000] text-[#ffffff] text-xs font-semibold rounded">
                      {t('ph_save')}
                    </button>
                    <button type="button" onClick={() => setAdding(false)} className="px-2 py-1 bg-[#eceef0] text-[#45464d] text-xs rounded">
                      {t('ph_cancel')}
                    </button>
                  </div>
                ) : (
                  <button data-testid="add-claim" onClick={() => setAdding(true)} type="button" className="py-1.5 px-3 bg-[#eceef0] text-[#191c1e] text-xs font-semibold rounded flex items-center justify-center gap-1 hover:bg-[#e0e3e5] transition-colors border border-[#c6c6cd]">
                    <Icon name="add" className="text-[16px]" />
                    <span>{t('ph_add')}</span>
                  </button>
                )}
                <div className="mt-auto flex justify-between items-center pt-3 border-t border-[#f2f4f6]">
                  <button onClick={() => setStep('upload')} type="button" className={back}>
                    {t('back')}
                  </button>
                  <button data-testid="continue" onClick={() => go('consent')} disabled={!allPicked || !claimset.claims.length || claimset.claims.some((c) => Object.entries(c.fields).some(([k, v]) => badFormat(k, v)))} type="button" className={fwd}>
                    <span>{t('ph_confirm')}</span>
                    <Icon name="arrow_forward" className="text-[14px]" />
                  </button>
                </div>
              </section>
            )}

            {step === 'consent' && (
              <section data-testid="consent" className="flex flex-col gap-3">
                <Kicker kicker={t('ph_kicker_4')} title={t('ph_gate')} desc={t('ph_gate_desc')} />
                <div className={panel}>
                  <div className="flex items-start gap-2">
                    <Icon name="shield" className="text-[#515f74] text-[20px] mt-0.5" />
                    <div className="flex flex-col">
                      <span className="text-xs font-bold text-[#191c1e]">{t('ph_retention')}</span>
                      <p className="text-[11px] text-[#45464d] leading-relaxed mt-0.5">{t('ph_retention_desc')}</p>
                    </div>
                  </div>
                  <div className="bg-[#ffffff] p-2 rounded flex items-center justify-between border border-[#e0e3e5]">
                    <span className="text-[11px] text-[#45464d]">{t('ph_target')}</span>
                    <span className="text-xs font-mono font-bold text-[#191c1e]">{t('ph_target_value')}</span>
                  </div>
                  <span className="text-[10px] text-[#45464d]">{t('consent_mock')}</span>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="otp" className="text-xs text-[#191c1e] font-semibold">
                    {t('ph_enter_otp')}
                  </label>
                  <div className="flex items-center gap-2">
                    <input id="otp" data-testid="otp" inputMode="numeric" maxLength={6} value={otp} onChange={(e) => setOtp(e.target.value)} className="w-full text-center tracking-widest font-mono font-bold text-base py-1.5 px-3 bg-[#f2f4f6] text-[#191c1e] rounded border border-[#c6c6cd] focus:outline-none focus:border-[#000000]" />
                    <button data-testid="otp-autofill" onClick={() => setOtp(MOCK_OTP)} type="button" className="py-2 px-3 bg-[#eceef0] text-[#191c1e] text-xs font-semibold rounded whitespace-nowrap hover:bg-[#e0e3e5] border border-[#c6c6cd]">
                      {t('ph_autofill')}
                    </button>
                  </div>
                  <span className="text-[10px] text-[#45464d]">{t('ph_otp_note')}</span>
                  {otpWrong && <span className="text-[11px] text-[#93000a]">{t('otp_wrong')}</span>}
                </div>
                <div className="flex flex-col gap-2 pt-2 border-t border-[#f2f4f6]">
                  <button data-testid="approve" onClick={() => check(['CDSL', 'NSDL'])} type="button" className={btn}>
                    <Icon name="lock_open" className="text-[16px]" />
                    <span>{t('ph_authorize')}</span>
                  </button>
                  <button data-testid="refuse" onClick={() => check([])} type="button" className="w-full py-2 bg-transparent text-[#515f74] text-xs hover:text-[#191c1e] text-center">
                    {t('ph_skip')}
                  </button>
                </div>
              </section>
            )}

            {step === 'checking' && (
              <section data-testid="step-checking" className="flex flex-col gap-3">
                <Kicker kicker={t('ph_kicker_5')} title={t('ph_querying')} desc={t('ph_querying_desc')} />
                <ul className="flex flex-col gap-2.5 py-1">
                  <StageRow title={t('progress_check')} stage={stages.check ?? 'waiting'} lang={lang} icon="rule" />
                  <StageRow title={t('progress_records', { count: records.length })} stage={stages.records ?? 'waiting'} lang={lang} icon="inventory" />
                </ul>
                {stages.records === 'done' && (
                  <ul data-testid="record-sources" className="flex flex-col gap-2">
                    {records.map((r) => (
                      <StageRow key={r.sha256} title={t('record_source', { source: r.source })} sub={`${t('record_fetched', { fetched_at: r.fetched_at })} · ${t(r.mock ? 'record_mock' : 'record_public')}`} stage="done" lang={lang} />
                    ))}
                  </ul>
                )}
                <div className="mt-auto pt-2 flex flex-col gap-2">
                  <button data-testid="next" onClick={() => go('result')} disabled={stages.records !== 'done'} type="button" className={btn}>
                    <span>{t(stages.records === 'done' ? 'ph_view_results' : 'ph_waiting_records')}</span>
                  </button>
                </div>
              </section>
            )}

            {step === 'result' && result && <ResultStep lang={lang} result={result} records={records} onBack={() => setStep('consent')} onNext={() => go('action')} />}
            {step === 'action' && result && claimset && <ActionStep lang={lang} result={result} claimset={claimset} customer={customer} onNext={() => go('pack')} />}
            {step === 'pack' && result && <PackStep lang={lang} result={result} customer={customer} onRestart={restart} />}
          </div>

          {/* home bar */}
          <div className="w-full py-2 bg-[#ffffff] flex justify-center border-t border-[#f2f4f6]">
            <div className="w-28 h-1 bg-[#45464d] rounded-full opacity-40" />
          </div>
        </div>
        <footer data-testid="mock-footer" className="mt-4 max-w-[430px] text-[11px] text-[#45464d] text-center">
          {t('mock_footer')}
        </footer>
      </div>
    </div>
  )
}
