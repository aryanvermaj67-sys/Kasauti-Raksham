import en from '../../backend/app/templates/messages_en.json'
import hi from '../../backend/app/templates/messages_hi.json'
import { formatInr } from './money.ts'

export type Lang = 'en' | 'hi'
export type Params = Record<string, unknown>
type Templates = { reason_codes: Record<string, { app: string; record: string }>; ui: Record<string, unknown> }

const T = { en, hi } as unknown as Record<Lang, Templates>
const AND: Record<Lang, string> = { en: ' and ', hi: ' और ' }

function show(key: string, v: unknown, lang: Lang): string {
  if (Array.isArray(v)) return v.length ? v.join(AND[lang]) : String(T[lang].ui.unknown)
  if (typeof v === 'number') return key.endsWith('_inr') ? formatInr(v, lang) : v.toLocaleString('en-IN')
  if (v === null || v === undefined || v === '') return String(T[lang].ui.unknown)
  return String(v)
}

/** Every user-facing sentence comes from messages_{en,hi}.json; this only fills {params}. */
export function fill(template: string, params: Params, lang: Lang): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => show(k, params[k], lang))
}

export const ui = (lang: Lang, key: string, params: Params = {}) => fill(String(T[lang].ui[key]), params, lang)

export function verdictText(lang: Lang, code: string, params: Params) {
  const m = T[lang].reason_codes[code]
  return { app: fill(m.app, params, lang), record: fill(m.record, params, lang) }
}
