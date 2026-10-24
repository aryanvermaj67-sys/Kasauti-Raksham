import assert from 'node:assert/strict'
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const SRC = fileURLToPath(new URL('.', import.meta.url))
const TEMPLATES = ['en', 'hi'].map((l) => JSON.parse(readFileSync(join(SRC, `../../backend/app/templates/messages_${l}.json`), 'utf8')))
const SENTENCES: string[] = TEMPLATES.flatMap((t) => [
  ...Object.values(t.reason_codes as Record<string, { app: string; record: string }>).flatMap((m) => [m.app, m.record]),
  ...Object.values(t.ui as Record<string, unknown>).filter((v): v is string => typeof v === 'string'),
])
const WORDS = /\p{L}{2,}\s+\p{L}{2,}/u // two or more words: prose, not an identifier or a key
const PROSE_ATTRS = new Set(['placeholder', 'title', 'alt', 'aria-label'])

function tsxFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? tsxFiles(join(dir, e.name)) : e.name.endsWith('.tsx') ? [join(dir, e.name)] : [],
  )
}

/** Text a component may not contain: JSX prose, prose strings in markup, template sentences, verdict-like words. */
function problems(code: string): string[] {
  const out: string[] = []
  const file = ts.createSourceFile('x.tsx', code, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
  const inMarkup = (n: ts.Node): boolean => !!n.parent && (ts.isJsxExpression(n.parent) || (!ts.isJsxAttribute(n.parent) && inMarkup(n.parent)))
  const visit = (n: ts.Node) => {
    if (ts.isJsxText(n) && WORDS.test(n.text)) out.push(`JSX text: ${n.text.trim()}`)
    if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) {
      const attr = ts.isJsxAttribute(n.parent) ? n.parent.name.getText(file) : null
      if (attr ? PROSE_ATTRS.has(attr) && /\p{L}{2,}/u.test(n.text) : inMarkup(n) && WORDS.test(n.text)) out.push(`string in markup: ${n.text}`)
    }
    ts.forEachChild(n, visit)
  }
  visit(file)
  for (const s of SENTENCES) for (const part of s.split(/\{\w+\}/)) if (part.trim().length >= 12 && code.includes(part.trim())) out.push(`template text: ${part.trim()}`)
  for (const m of code.matchAll(/\b(verified|safe|genuine|score)\b|\d+\s*%/gi)) out.push(`banned word: ${m[0]}`)
  return out
}

test('a planted hard-coded sentence in a real component fails the check', () => {
  const original = readFileSync(join(SRC, 'components', 'ResultScreen.tsx'), 'utf8')
  assert.deepEqual(problems(original), [])
  const anchor = '<h2 className="text-lg font-semibold">'
  assert.ok(original.includes(anchor))
  const plants = [
    '<p>Not in your name at CDSL and NSDL.</p>', // a template sentence copied into markup
    '<p>Your broker is fake (we checked) = done;</p>', // new prose with ( ) = ;
    "<p>{'This app is a scam.'}</p>", // prose as a string expression
    "<p>{ok ? 'All good here' : 'Do not pay'}</p>", // prose in a ternary
    '<input placeholder="Type the OTP here" />', // prose in an attribute
    '<p>Verified</p>', // verdict-like word
  ]
  for (const plant of plants) {
    const planted = original.replace(anchor, `${plant}\n      ${anchor}`)
    assert.ok(problems(planted).length > 0, `not caught: ${plant}`)
  }
})

test('components take every sentence from messages_en.json / messages_hi.json', () => {
  const files = tsxFiles(SRC)
  assert.ok(files.some((f) => f.endsWith('ResultScreen.tsx')))
  for (const f of files) assert.deepEqual(problems(readFileSync(f, 'utf8')), [], f)
})
