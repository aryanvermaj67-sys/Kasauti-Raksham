import { Scale, Search, TriangleAlert } from 'lucide-react'
import type { Outcome } from '../api.ts'
import { ui, type Lang } from '../i18n.ts'

// the spec's three verification states: always icon + label + border, never colour alone
export const TONE: Record<Outcome, { icon: typeof Scale; box: string }> = {
  CONTRADICTS: { icon: TriangleAlert, box: 'border-contra-line bg-contra-bg text-contra' },
  MATCHES: { icon: Scale, box: 'border-match-line bg-match-bg text-match' },
  NO_RECORD: { icon: Search, box: 'border-norec-line bg-norec-bg text-norec' },
}

export default function OutcomeChip({ outcome, lang }: { outcome: Outcome; lang: Lang }) {
  const { icon: Icon, box } = TONE[outcome]
  return (
    <span data-testid="outcome-chip" data-outcome={outcome} className={`inline-flex items-center gap-1 rounded-box border px-2 py-1 text-xs font-bold tracking-wide ${box}`}>
      <Icon size={16} aria-hidden />
      {ui(lang, `outcome_${outcome}`)}
    </span>
  )
}
