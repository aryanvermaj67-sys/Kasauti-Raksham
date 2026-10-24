import { CircleAlert, CircleCheck, Loader } from 'lucide-react'
import { useEffect, useState } from 'react'
import { health } from '../api.ts'
import { ui, type Lang } from '../i18n.ts'

export type Health = 'ready' | 'preparing' | 'down'

/** Polls /api/health until ready; "preparing" while models load, "down" while the backend does not answer. */
export function useHealth(): Health {
  const [state, setState] = useState<Health>('preparing')
  useEffect(() => {
    let stop = false
    const poll = () =>
      health()
        .then((h) => (h.ready ? 'ready' : 'preparing'))
        .catch(() => 'down' as const)
        .then((s) => {
          if (stop) return
          setState(s)
          if (s !== 'ready') setTimeout(poll, 1000)
        })
    poll()
    return () => {
      stop = true
    }
  }, [])
  return state
}

export function useLarge(): [boolean, (v: boolean) => void] {
  const [large, setLarge] = useState(false)
  useEffect(() => {
    document.documentElement.dataset.large = large ? '1' : '0'
  }, [large])
  return [large, setLarge]
}

const chip = 'inline-flex min-h-11 items-center gap-1 rounded-box border px-2 text-sm font-semibold'
const ON = 'border-ink bg-ink text-white'
const OFF = 'border-line-2 bg-white'
const STATUS = {
  ready: { icon: CircleCheck, cls: 'border-match-line bg-match-bg text-match', key: 'status_ready' },
  preparing: { icon: Loader, cls: 'border-line-2 bg-panel text-muted', key: 'status_preparing' },
  down: { icon: CircleAlert, cls: 'border-contra-line bg-contra-bg text-contra', key: 'status_down' },
}

type Props = { lang: Lang; setLang: (l: Lang) => void; large: boolean; setLarge: (v: boolean) => void; status: Health; onReset: () => void }

export default function Header({ lang, setLang, large, setLarge, status, onReset }: Props) {
  const t = (key: string) => ui(lang, key)
  const s = STATUS[status]
  return (
    <header className="border-b border-line bg-white px-4 py-2">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="mr-auto text-lg font-bold">{t('app_title')}</h1>
        <span data-testid="synthetic-chip" className={`${chip} border-ink bg-white text-ink tracking-wide`}>
          {t('synthetic_chip')}
        </span>
        <span data-testid="status-chip" data-status={status} className={`${chip} ${s.cls}`}>
          <s.icon size={16} aria-hidden />
          {t(s.key)}
        </span>
        <button data-testid="lang-toggle" className={`${chip} border-line-2 bg-white`} onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}>
          {t('lang_toggle')}
        </button>
        <button
          data-testid="large-toggle"
          aria-pressed={large}
          aria-label={t('large_text_label')}
          className={`${chip} ${large ? ON : OFF}`}
          onClick={() => setLarge(!large)}
        >
          {t('large_text')}
        </button>
        <button data-testid="reset" className={`${chip} border-line-2 bg-white`} onClick={onReset}>
          {t('reset')}
        </button>
      </div>
    </header>
  )
}
