import { useEffect, useState } from 'react'
import ResultScreen from '../components/ResultScreen.tsx'
import {
  CUSTOMER,
  ackPrompt,
  health,
  isinCandidates,
  triggerPrompts,
  type Prompt,
  readArtifact,
  runCheck,
  uploadVideo,
  type Candidate,
  type CheckResult,
  type Claim,
  type ClaimSet,
  type FieldValue,
} from '../api.ts'
import { ui, type Lang, type Params } from '../i18n.ts'

type Step = 'home' | 'upload' | 'confirm' | 'consent' | 'checking' | 'result'
const NUMBER_FIELDS = ['quantity', 'value_inr']
const BOOL_FIELDS = ['claims_registered', 'claims_licensed']
const SELECT_FIELDS: Record<string, string[]> = { described_as: ['broker', 'advisor', 'other'], category: ['equity', 'forex', 'crypto', 'other'] }
const HIDDEN_FIELDS = ['media_sha256']
const MOCK_OTP = '123456'
const btn = 'rounded-lg bg-blue-800 px-4 py-3 font-semibold text-white disabled:opacity-40'
const input = 'w-full rounded border border-slate-300 px-2 py-1'

export default function BankApp() {
  const [lang, setLang] = useState<Lang>('en')
  const [step, setStep] = useState<Step>('home')
  const [shot, setShot] = useState<File | null>(null)
  const [video, setVideo] = useState<File | null>(null)
  const [claimset, setClaimset] = useState<ClaimSet | null>(null)
  const [choices, setChoices] = useState<Record<string, Candidate[]>>({})
  const [picked, setPicked] = useState<Record<string, string>>({})
  const [otp, setOtp] = useState('')
  const [otpWrong, setOtpWrong] = useState(false)
  const [result, setResult] = useState<CheckResult | null>(null)
  const [error, setError] = useState('')
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [ready, setReady] = useState(false)
  useEffect(() => {
    // models load after the backend starts; until then (or while it is still starting) show "preparing", never an error
    const poll = () => health().then((h) => h.ready).catch(() => false).then((r) => (r ? setReady(true) : void setTimeout(poll, 1000)))
    poll()
  }, [])
  useEffect(() => {
    triggerPrompts(CUSTOMER.id).then(setPrompts).catch(() => setPrompts([])) // a failed trigger never blocks the app
  }, [])
  const t = (key: string, params?: Params) => ui(lang, key, params)

  const fail = (e: unknown) => setError(t('error', { error: e instanceof Error ? e.message : String(e) }))

  async function resolveIsin(claim: Claim) {
    const name = String(claim.fields.instrument_name ?? '')
    const found = name ? await isinCandidates(name) : []
    setChoices((c) => {
      const { [claim.id]: _old, ...rest } = c
      void _old
      return found.length > 1 ? { ...rest, [claim.id]: found } : rest
    })
    setPicked(({ [claim.id]: _old, ...rest }) => (void _old, rest))
    setField(claim.id, 'isin', found.length === 1 ? found[0].isin : null)
  }

  async function read() {
    if (!shot) return
    setError('')
    setStep('checking')
    try {
      const cs = await readArtifact(shot)
      if (video) {
        const { media_sha256, match } = await uploadVideo(video)
        // the words changed from the source are the claim; with no change or no source, the opening words
        const quote = match.quote || match.transcript.split(' ').slice(0, 25).join(' ')
        cs.claims.push({ id: `c${cs.claims.length + 1}`, type: 'endorsement', fields: { person: '', quote, media_sha256 } })
      }
      setClaimset(cs)
      setChoices({})
      setPicked({})
      setStep('confirm')
      await Promise.all(cs.claims.filter((c) => c.type === 'holding' && c.fields.isin === null).map(resolveIsin))
    } catch (e) {
      fail(e)
      setStep('upload')
    }
  }

  function setField(id: string, key: string, value: FieldValue) {
    setClaimset((cs) => cs && { ...cs, claims: cs.claims.map((c) => (c.id === id ? { ...c, fields: { ...c.fields, [key]: value } } : c)) })
  }

  function pick(id: string, isin: string) {
    setPicked((p) => ({ ...p, [id]: isin }))
    setField(id, 'isin', isin || null) // '' means the customer skipped the choice: the check returns HOLDING_NAME_AMBIGUOUS
  }

  async function approve() {
    if (otp !== MOCK_OTP) return setOtpWrong(true)
    setOtpWrong(false)
    setStep('checking')
    try {
      setResult(await runCheck(claimset!, `consent-mock-${crypto.randomUUID().slice(0, 8)}`))
      setStep('result')
    } catch (e) {
      fail(e)
      setStep('consent')
    }
  }

  function restart() {
    setStep('home')
    setShot(null)
    setVideo(null)
    setClaimset(null)
    setResult(null)
    setOtp('')
  }

  const allPicked = Object.keys(choices).every((id) => id in picked)

  return (
    <div lang={lang} className="mx-auto min-h-screen max-w-md bg-slate-50 p-4 text-slate-900">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">{t('app_title')}</h1>
        <button data-testid="lang-toggle" className="rounded border px-3 py-1" onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}>
          {t('lang_toggle')}
        </button>
      </header>
      <p className="mb-4 text-sm text-slate-600">{t('signed_in', { customer: CUSTOMER.name })}</p>
      {error && <p className="mb-4 rounded bg-red-100 p-2 text-red-800">{error}</p>}

      {step === 'home' && prompts[0] && (
        <div data-testid="trigger-banner" className="mb-4 rounded-lg border-2 border-amber-500 bg-amber-50 p-3">
          <p className="font-semibold">{t('trigger_title')}</p>
          <p className="mt-1">{t(`trigger_${prompts[0].reason}`, { payee: prompts[0].payee })}</p>
          <p className="mt-1 text-sm">{t('trigger_not_blocked')}</p>
          <button
            data-testid="trigger-dismiss"
            className="mt-2 rounded border px-3 py-1"
            onClick={() => ackPrompt(CUSTOMER.id, prompts[0].campaign).then(() => setPrompts((p) => p.slice(1)))}
          >
            {t('trigger_dismiss')}
          </button>
        </div>
      )}

      {step === 'home' && !ready && <p data-testid="preparing" className="rounded bg-amber-50 p-3">{t('preparing')}</p>}
      {step === 'home' && (
        <button data-testid="check-button" className={`${btn} w-full`} disabled={!ready} onClick={() => setStep('upload')}>
          {t('check_button')}
        </button>
      )}

      {step === 'upload' && (
        <section className="space-y-4">
          <h2 className="font-semibold">{t('upload_title')}</h2>
          <label className="block">
            <span className="text-sm">{t('upload_screenshot')}</span>
            <input data-testid="shot-input" type="file" accept="image/png,image/jpeg" className={input} onChange={(e) => setShot(e.target.files?.[0] ?? null)} />
          </label>
          <label className="block">
            <span className="text-sm">{t('upload_video')}</span>
            <input data-testid="video-input" type="file" accept="video/mp4" className={input} onChange={(e) => setVideo(e.target.files?.[0] ?? null)} />
          </label>
          {video && <p className="text-sm text-slate-600">{t('video_note')}</p>}
          <button data-testid="read-button" className={`${btn} w-full`} disabled={!shot} onClick={read}>
            {t('read_button')}
          </button>
        </section>
      )}

      {step === 'checking' && <p className="py-8 text-center">{t(claimset ? 'checking' : 'reading')}</p>}

      {step === 'confirm' && claimset && (
        <section data-testid="confirm" className="space-y-4">
          <h2 className="font-semibold">{t('confirm_title')}</h2>
          {claimset.claims.map((c) => (
            <fieldset key={c.id} className="rounded-lg border bg-white p-3">
              <legend className="px-1 text-sm font-semibold">{t(`claim_${c.type}`)}</legend>
              {Object.entries(c.fields)
                .filter(([k]) => !HIDDEN_FIELDS.includes(k))
                .map(([k, v]) => (
                  <label key={k} className="mb-2 block">
                    <span className="text-xs text-slate-600">{t(`field_${k}`)}</span>
                    {BOOL_FIELDS.includes(k) ? (
                      <input type="checkbox" className="ml-2" checked={Boolean(v)} onChange={(e) => setField(c.id, k, e.target.checked)} />
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
                <div data-testid={`choices-${c.id}`} className="mt-2 rounded bg-amber-50 p-2">
                  <p className="text-sm">{t('ambiguous_pick')}</p>
                  {[...choices[c.id], { isin: '', name: t('skip_choice') }].map((o) => (
                    <label key={o.isin || 'skip'} className="block text-sm">
                      <input type="radio" name={`pick-${c.id}`} checked={picked[c.id] === o.isin} onChange={() => pick(c.id, o.isin)} />{' '}
                      {o.isin ? `${o.isin} · ${o.name}` : o.name}
                    </label>
                  ))}
                </div>
              )}
            </fieldset>
          ))}
          <button data-testid="continue" className={`${btn} w-full`} disabled={!allPicked} onClick={() => setStep('consent')}>
            {t('continue')}
          </button>
        </section>
      )}

      {step === 'consent' && (
        <section data-testid="consent" className="space-y-4 rounded-lg border-2 border-dashed border-amber-500 bg-white p-4">
          <p className="inline-block rounded bg-amber-500 px-2 py-0.5 text-sm font-bold text-white">{t('mock')}</p>
          <h2 className="font-semibold">{t('consent_title')}</h2>
          <p className="text-sm">{t('consent_mock')}</p>
          <p className="text-sm">{t('consent_body')}</p>
          <label className="block">
            <span className="text-sm">{t('otp_label')}</span>
            <input data-testid="otp" inputMode="numeric" maxLength={6} className={input} value={otp} onChange={(e) => setOtp(e.target.value)} />
          </label>
          {otpWrong && <p className="text-sm text-red-700">{t('otp_wrong')}</p>}
          <button data-testid="approve" className={`${btn} w-full`} onClick={approve}>
            {t('approve')}
          </button>
        </section>
      )}

      {step === 'result' && result && claimset && <ResultScreen lang={lang} result={result} claimset={claimset} onRestart={restart} />}
      <footer data-testid="mock-footer" className="mt-6 text-xs text-slate-500">{t('mock_footer')}</footer>
    </div>
  )
}
