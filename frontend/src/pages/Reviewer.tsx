import { ui } from '../i18n.ts'

export default function Reviewer() {
  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="text-2xl font-bold">{ui('en', 'reviewer_title')}</h1>
      <p className="mt-2 text-slate-600">{ui('en', 'reviewer_placeholder')}</p>
    </main>
  )
}
