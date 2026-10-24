import { useEffect, useState } from 'react'
import { demo, type Scenario } from '../api.ts'
import { ui, type Lang, type Params } from '../i18n.ts'

// header buttons size to their text (the shared phone buttons are full width)
const bar = 'inline-flex min-h-11 items-center rounded-box border px-3 font-semibold disabled:opacity-40'
const barDark = `${bar} border-ink bg-ink text-white`
const barLight = `${bar} border-line-2 bg-white`

/** Phone and console side by side. They share no React state: each page polls the backend, so what one does the
 * other sees through the API, exactly as on two devices. */
export default function Present() {
  const [lang, setLang] = useState<Lang>('en')
  const [list, setList] = useState<Scenario[]>([])
  const [enabled, setEnabled] = useState(false)
  const [phone, setPhone] = useState('')
  const [note, setNote] = useState('')
  const [epoch, setEpoch] = useState(0) // bumps after a reset so both pages reload
  const t = (key: string, params?: Params) => ui(lang, key, params)

  useEffect(() => {
    demo
      .mode()
      .then((m) => {
        setEnabled(m.demo_mode)
        setList(m.scenarios)
      })
      .catch((e) => setNote(t('error', { error: String(e) })))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function run(id: string) {
    setPhone(id)
    const r = await demo.run(id) // a real run on the demo artifact; the console picks it up on its next poll
    setNote(t('present_started', { id: r.scenario, check_id: r.check_id }))
  }

  async function reset() {
    await demo.reset()
    setNote('')
    setEpoch((e) => e + 1)
  }

  const q = `lang=${lang}&v=${epoch}`
  return (
    <div lang={lang} className="min-h-screen bg-canvas">
      <header className="flex flex-wrap items-center gap-2 border-b border-line bg-white px-4 py-2">
        <h1 className="mr-auto text-lg font-bold">{t('present_title')}</h1>
        {list.map((s) => (
          <button key={s.id} data-testid={`present-run-${s.id}`} className={barLight} disabled={!enabled} onClick={() => run(s.id).catch((e) => setNote(String(e)))}>
            {t('present_run', { id: s.id })}
          </button>
        ))}
        <button data-testid="present-lang" className={barLight} onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}>
          {t('lang_toggle')}
        </button>
        <button data-testid="present-reset" className={barDark} disabled={!enabled} onClick={() => reset().catch((e) => setNote(String(e)))}>
          {t('present_reset')}
        </button>
      </header>
      {!enabled && <p className="bg-panel px-4 py-2 text-sm">{t('present_reset_off')}</p>}
      {note && (
        <p data-testid="present-note" className="px-4 py-2 text-sm">
          {note}
        </p>
      )}
      <main className="grid gap-4 p-4 lg:grid-cols-[440px_1fr]">
        <section>
          <h2 className="mb-2 font-semibold">{t('present_phone')}</h2>
          <iframe
            key={`phone-${phone}-${q}`}
            title={t('present_phone')}
            data-testid="present-phone"
            src={`/app?${phone ? `scenario=${phone}&` : ''}${q}`}
            className="h-[860px] w-full rounded-lg border border-line bg-white"
          />
        </section>
        <section>
          <h2 className="mb-2 font-semibold">{t('present_console')}</h2>
          <iframe key={`console-${q}`} title={t('present_console')} data-testid="present-console" src={`/reviewer?${q}`} className="h-[860px] w-full rounded-lg border border-line bg-white" />
        </section>
      </main>
    </div>
  )
}
