import { Check, Loader, Plus, Trash2 } from 'lucide-react'
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
export const btn = 'inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-box bg-ink px-4 py-2 font-semibold text-white hover:bg-ink-2 disabled:opacity-40'
export const btn2 = 'inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-box border border-line-2 bg-white px-4 py-2 font-semibold text-ink'
const input = 'min-h-12 w-full rounded-box border border-line-2 px-3 text-base focus:border-ink focus:outline-none'
const card = 'rounded-box border border-line bg-white p-4'

function StageRow({ label, stage, lang }: { label: string; stage: Stage; lang: Lang }) {
  const Icon = stage === 'done' ? Check : Loader
  return (
    <li data-testid="stage" data-stage={stage} className={`flex min-h-11 items-center gap-2 ${card}`}>
      <Icon size={18} aria-hidden className={stage === 'running' ? 'animate-spin' : ''} />
      <span className="mr-auto">{label}</span>
      <span className="text-sm text-muted">{ui(lang, `progress_${stage}`)}</span>
    </li>
  )
}

export default function CustomerApp() {
  const [lang, setLang] = useState<Lang>(params.get('lang') === 'hi' ? 'hi' : 'en')
  const [large, setLarge] = useLarge()
  const status = useHealth()
  const [step, setStep] = useState<Step>('payment')
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
  const [otp, setOtp] = useState('')
  const [otpWrong, setOtpWrong] = useState(false)
  const [stages, setStages] = useState<Record<string, Stage>>({})
  const [result, setResult] = useState<CheckResult | null>(null)
  const [records, setRecords] = useState<RecordSummary[]>([])
  const [error, setError] = useState('')
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const t = (key: string, params?: Params) => ui(lang, key, params)
  const fail = (e: unknown) => setError(t('error', { error: e instanceof Error ? e.message : String(e) }))
  const stage = (k: string, s: Stage) => setStages((x) => ({ ...x, [k]: s }))

  useEffect(() => {
    scenarios()
      .then((s) => {
        setList(s)
        const wanted = s.find((x) => x.id === params.get('scenario'))
        if (wanted || (!URL_CUSTOMER && s[0])) choose(wanted ?? s[0])
      })
      .catch(fail)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  useEffect(() => {
    if (customer) triggerPrompts(customer).then(setPrompts).catch(() => setPrompts([])) // a failed trigger never blocks the app
  }, [customer])

  function choose(s: Scenario) {
    setScenario(s)
    setCustomer(s.customer_id)
    setPayee(s.payment_request?.payee ?? '')
    setShot(null)
    setVideo(null)
  }

  async function loadScenarioFiles() {
    if (!scenario) return
    setShot(await demoFile(scenario.screenshot))
    setVideo(scenario.video ? await demoFile(scenario.video) : null)
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
      setStep('confirm')
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
  function addClaim(type: string) {
    setClaimset((cs) => {
      if (!cs) return cs
      const n = Math.max(0, ...cs.claims.map((c) => Number(c.id.slice(1)) || 0)) + 1
      return { ...cs, claims: [...cs.claims, { id: `c${n}`, type: type as Claim['type'], fields: { ...BLANK[type] } }] }
    })
  }
  function pick(id: string, isin: string) {
    setPicked((p) => ({ ...p, [id]: isin }))
    setField(id, 'isin', isin || null) // '' means the customer skipped the choice: the check returns HOLDING_NAME_AMBIGUOUS
  }

  async function check(scope: string[]) {
    if (scope.length && otp !== MOCK_OTP) return setOtpWrong(true)
    setOtpWrong(false)
    setError('')
    setStep('checking')
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
  const next = (s: Step) => (
    <button data-testid="next" className={btn} onClick={() => setStep(s)}>
      {t('next')}
    </button>
  )

  return (
    <div lang={lang} className="min-h-screen bg-canvas">
      <Header lang={lang} setLang={setLang} large={large} setLarge={setLarge} status={status} onReset={restart} />
      <main className="mx-auto max-w-[430px] p-4">
        <div className="mb-4 rounded-lg border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <p data-testid="step-title" className="font-semibold">
              {t('step_of', { n: idx + 1, total: STEPS.length, name: t(`step_${step}`) })}
            </p>
            <ol className="mt-2 grid grid-cols-8 gap-1" aria-hidden>
              {STEPS.map((s, i) => (
                <li key={s} className={`h-1.5 rounded-box ${i <= idx ? 'bg-ink' : 'bg-line'}`} />
              ))}
            </ol>
            <p className="mt-2 text-sm text-muted">{customer && t('signed_in', { customer })}</p>
          </div>

          <div className="space-y-4 p-4">
            {error && <p className="rounded-box border border-contra-line bg-contra-bg p-3 text-contra">{error}</p>}

            {step === 'payment' && (
              <section data-testid="step-payment" className="space-y-4">
                {list.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-muted">{t('scenario_title')}</p>
                    {list.map((s) => (
                      <button
                        key={s.id}
                        data-testid={`scenario-${s.id}`}
                        aria-pressed={scenario?.id === s.id}
                        className={`${btn2} justify-start text-left ${scenario?.id === s.id ? 'border-ink' : ''}`}
                        onClick={() => choose(s)}
                      >
                        {t('scenario_pick', { id: s.id, customer: s.customer_id })} {s.video && `· ${t('scenario_video')}`}
                      </button>
                    ))}
                  </div>
                )}
                {prompts[0] && (
                  <div data-testid="trigger-banner" className="rounded-box border border-contra-line bg-contra-bg p-3 text-contra">
                    <p className="font-semibold">{t('trigger_title')}</p>
                    <p className="mt-1">{t(`trigger_${prompts[0].reason}`, { payee: prompts[0].payee })}</p>
                    <p className="mt-1 text-sm">{t('trigger_not_blocked')}</p>
                    <button
                      data-testid="trigger-dismiss"
                      className={`${btn2} mt-2`}
                      onClick={() => ackPrompt(customer, prompts[0].campaign).then(() => setPrompts((p) => p.slice(1)))}
                    >
                      {t('trigger_dismiss')}
                    </button>
                  </div>
                )}
                <div className={card}>
                  <h2 className="mb-3 text-lg font-semibold">{t('payment_title')}</h2>
                  <label className="mb-3 block">
                    <span className="text-sm text-muted">{t('payment_payee')}</span>
                    <input data-testid="payment-payee" className={input} value={payee} onChange={(e) => setPayee(e.target.value)} />
                  </label>
                  {scenario?.payment_request && <p className="mb-3 text-sm text-muted">{t('payment_prefilled')}</p>}
                  <label className="block">
                    <span className="text-sm text-muted">{t('payment_amount')}</span>
                    <input data-testid="payment-amount" inputMode="numeric" className={input} value={amount} onChange={(e) => setAmount(e.target.value)} />
                  </label>
                </div>
                <p className="font-semibold">{t('payment_check_first')}</p>
                {status !== 'ready' && (
                  <p data-testid="preparing" className="rounded-box border border-line-2 bg-panel p-3">
                    {t('preparing')}
                  </p>
                )}
                <button data-testid="check-button" className={btn} disabled={status !== 'ready' || !customer} onClick={() => setStep('upload')}>
                  {t('check_button')}
                </button>
                <button data-testid="pay-skip" className={btn2} onClick={() => setSkipped(true)}>
                  {t('payment_skip')}
                </button>
                {skipped && <p className="text-sm">{t('still_pay_note')}</p>}
              </section>
            )}

            {step === 'upload' && (
              <section data-testid="step-upload" className="space-y-4">
                <h2 className="text-lg font-semibold">{t('upload_title')}</h2>
                {scenario && (
                  <button data-testid="use-scenario" className={btn2} onClick={() => loadScenarioFiles().catch(fail)}>
                    {t('scenario_pick', { id: scenario.id, customer: scenario.customer_id })}
                  </button>
                )}
                <label className="block">
                  <span className="text-sm text-muted">{t('upload_screenshot')}</span>
                  <input data-testid="shot-input" type="file" accept="image/png,image/jpeg" className={input} onChange={(e) => setShot(e.target.files?.[0] ?? null)} />
                  {shot && <span className="text-sm">{shot.name}</span>}
                </label>
                <label className="block">
                  <span className="text-sm text-muted">{t('upload_video')}</span>
                  <input data-testid="video-input" type="file" accept="video/mp4" className={input} onChange={(e) => setVideo(e.target.files?.[0] ?? null)} />
                  {video && <span className="text-sm">{video.name}</span>}
                </label>
                {video && <p className="text-sm text-muted">{t('video_note')}</p>}
                {Object.keys(stages).length > 0 && (
                  <ul className="space-y-2">
                    {stages.read && <StageRow label={t('progress_read')} stage={stages.read} lang={lang} />}
                    {stages.video && <StageRow label={t('progress_video')} stage={stages.video} lang={lang} />}
                  </ul>
                )}
                <button data-testid="read-button" className={btn} disabled={!shot || stages.read === 'running'} onClick={read}>
                  {t('read_button')}
                </button>
                <button className={btn2} onClick={() => setStep('payment')}>
                  {t('back')}
                </button>
              </section>
            )}

            {step === 'confirm' && claimset && (
              <section data-testid="confirm" className="space-y-4">
                <h2 className="text-lg font-semibold">{t('confirm_title')}</h2>
                {claimset.claims.map((c) => (
                  <fieldset key={c.id} data-testid={`claim-${c.id}`} className={card}>
                    <legend className="px-1 text-sm font-semibold">{t(`claim_${c.type}`)}</legend>
                    {Object.entries(c.fields)
                      .filter(([k]) => !HIDDEN_FIELDS.includes(k))
                      .map(([k, v]) => (
                        <label key={k} className="mb-2 block">
                          <span className="text-sm text-muted">{t(`field_${k}`)}</span>
                          {BOOL_FIELDS.includes(k) ? (
                            <input type="checkbox" className="ml-2 size-[18px] accent-ink" checked={Boolean(v)} onChange={(e) => setField(c.id, k, e.target.checked)} />
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
                              onChange={(e) => setField(c.id, k, NUMBER_FIELDS.includes(k) ? (e.target.value === '' ? null : Number(e.target.value)) : e.target.value || null)}
                              onBlur={k === 'instrument_name' ? () => resolveIsin(c).catch(fail) : undefined}
                            />
                          )}
                        </label>
                      ))}
                    {choices[c.id] && (
                      <div data-testid={`choices-${c.id}`} className="mt-2 rounded-box border border-line-2 bg-panel p-2">
                        <p className="text-sm">{t('ambiguous_pick')}</p>
                        {[...choices[c.id], { isin: '', name: t('skip_choice') }].map((o) => (
                          <label key={o.isin || 'skip'} className="flex min-h-11 items-center gap-2 text-sm">
                            <input type="radio" name={`pick-${c.id}`} checked={picked[c.id] === o.isin} onChange={() => pick(c.id, o.isin)} />
                            {o.isin ? `${o.isin} · ${o.name}` : o.name}
                          </label>
                        ))}
                      </div>
                    )}
                    <button data-testid={`remove-${c.id}`} className={`${btn2} mt-2`} onClick={() => removeClaim(c.id)}>
                      <Trash2 size={16} aria-hidden /> {t('remove_claim')}
                    </button>
                  </fieldset>
                ))}
                <div className="grid grid-cols-2 gap-2">
                  {Object.keys(BLANK).map((type) => (
                    <button key={type} data-testid={`add-${type}`} className={btn2} onClick={() => addClaim(type)}>
                      <Plus size={16} aria-hidden /> {t(`claim_${type}`)}
                    </button>
                  ))}
                </div>
                <p className="sr-only">{t('add_claim')}</p>
                <button data-testid="continue" className={btn} disabled={!allPicked || !claimset.claims.length} onClick={() => setStep('consent')}>
                  {t('continue')}
                </button>
              </section>
            )}

            {step === 'consent' && (
              <section data-testid="consent" className="space-y-4 rounded-box border border-dashed border-line-2 bg-white p-4">
                <p className="inline-block rounded-box border border-ink px-2 py-0.5 text-sm font-bold">{t('mock')}</p>
                <h2 className="text-lg font-semibold">{t('consent_title')}</h2>
                <p>{t('consent_depositories')}</p>
                <p className="text-sm">{t('consent_mock')}</p>
                <p className="text-sm">{t('consent_body')}</p>
                <label className="block">
                  <span className="text-sm text-muted">{t('otp_label')}</span>
                  <input data-testid="otp" inputMode="numeric" maxLength={6} className={input} value={otp} onChange={(e) => setOtp(e.target.value)} />
                </label>
                {otpWrong && <p className="text-sm text-contra">{t('otp_wrong')}</p>}
                <button data-testid="approve" className={btn} onClick={() => check(['CDSL', 'NSDL'])}>
                  {t('approve')}
                </button>
                <button data-testid="refuse" className={btn2} onClick={() => check([])}>
                  {t('refuse')}
                </button>
              </section>
            )}

            {step === 'checking' && (
              <section data-testid="step-checking" className="space-y-4">
                <ul className="space-y-2">
                  <StageRow label={t('progress_check')} stage={stages.check ?? 'waiting'} lang={lang} />
                  <StageRow label={t('progress_records', { count: records.length })} stage={stages.records ?? 'waiting'} lang={lang} />
                </ul>
                {stages.records === 'done' && (
                  <ul data-testid="record-sources" className="space-y-1 text-sm text-muted">
                    {records.map((r) => (
                      <li key={r.sha256}>
                        {t('record_source', { source: r.source })} · {t(r.mock ? 'record_mock' : 'record_public')}
                      </li>
                    ))}
                  </ul>
                )}
                {stages.records === 'done' && next('result')}
              </section>
            )}

            {step === 'result' && result && <ResultStep lang={lang} result={result} records={records} onNext={() => setStep('action')} />}
            {step === 'action' && result && claimset && (
              <ActionStep lang={lang} result={result} claimset={claimset} customer={customer} onNext={() => setStep('pack')} />
            )}
            {step === 'pack' && result && <PackStep lang={lang} result={result} customer={customer} onRestart={restart} />}
          </div>
        </div>
        <footer data-testid="mock-footer" className="text-sm text-muted">
          {t('mock_footer')}
        </footer>
      </main>
    </div>
  )
}
