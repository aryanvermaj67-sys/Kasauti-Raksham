import assert from 'node:assert/strict'
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

const SRC = fileURLToPath(new URL('.', import.meta.url))
const T = Object.fromEntries(['en', 'hi'].map((l) => [l, JSON.parse(readFileSync(join(SRC, `../../backend/app/templates/messages_${l}.json`), 'utf8'))]))
const code = (dir: string): [string, string][] =>
  readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? code(join(dir, e.name)) : /\.tsx?$/.test(e.name) && !e.name.endsWith('.test.ts') ? [[e.name, readFileSync(join(dir, e.name), 'utf8')] as [string, string]] : [],
  )
const FILES = code(SRC)

test('the only outcome identifiers in src are MATCHES, CONTRADICTS and NO_RECORD', () => {
  const found = new Set(FILES.flatMap(([, c]) => [...c.matchAll(/'([A-Z][A-Z_]{4,})'/g)].map((m) => m[1])))
  assert.deepEqual([...found].filter((w) => !['MATCHES', 'CONTRADICTS', 'NO_RECORD'].includes(w)), [])
  assert.equal(T.en.ui.outcome_CONTRADICTS, 'CONTRADICTS THE RECORD')
  assert.equal(T.en.ui.outcome_MATCHES, 'MATCHES THE RECORD')
  assert.equal(T.en.ui.outcome_NO_RECORD, 'NO RECORD FOUND')
})

test('no forbidden wording, demo figures or network URLs in app code or UI strings', () => {
  const banned = /\b(altered|source altered|partial match|high discrepancy|synthetic voice|safe|verified|genuine|fake|gemini)\b/i
  const figures = /Zyphra|39800000|3,98,00,000|3\.98 cr/i
  // real people, agencies and brands the design export used; every source shown must be a connector we have
  const brands = /minister|PIB|sansad|SBI|State Bank|AMFI|CAMS|sachet|ICICI|HDFC|Axis Bank|Kotak|Yes Bank|Bharat Bank|Lok Sabha/i
  for (const [name, c] of FILES) {
    assert.doesNotMatch(c, banned, name)
    assert.doesNotMatch(c, figures, name)
    assert.doesNotMatch(c, brands, name)
    const urls = [...c.matchAll(/https?:\/\/[^\s'"`]+/g)].map((m) => m[0])
    assert.deepEqual(urls.filter((u) => u !== 'https://cybercrime.gov.in'), [], name) // the one link opens only when tapped
  }
  for (const l of ['en', 'hi']) for (const [k, v] of Object.entries(T[l].ui)) {
    assert.doesNotMatch(String(v), banned, `${l}.ui.${k}`)
    assert.doesNotMatch(String(v), brands, `${l}.ui.${k}`)
  }
})

test('English and Hindi strings have the same keys and the same {placeholders}', () => {
  const holes = (s: string) => [...String(s).matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(',')
  for (const part of ['ui', 'reason_codes']) {
    const keys = (o: object) => Object.keys(o).filter((k) => !k.startsWith('_')).sort() // _needs_native_review is metadata
    assert.deepEqual(keys(T.hi[part]), keys(T.en[part]), part)
    for (const k of keys(T.en[part])) {
      const [en, hi] = [T.en[part][k], T.hi[part][k]]
      if (typeof en === 'string') assert.equal(holes(hi), holes(en), `${part}.${k}`)
      else for (const f of ['app', 'record']) assert.equal(holes(hi[f]), holes(en[f]), `${part}.${k}.${f}`)
    }
  }
})
