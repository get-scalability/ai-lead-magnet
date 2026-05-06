import type { Company } from '../types'

const ICP_SCORE_HIGH = 70
const ICP_SCORE_MID = 40

function scoreStyle(score: number): string {
  if (score >= ICP_SCORE_HIGH) return 'bg-green-100 text-green-800'
  if (score >= ICP_SCORE_MID) return 'bg-yellow-100 text-yellow-800'
  return 'bg-ag-bg-tertiary text-ag-text-muted'
}

export function IcpScoreBadge({ company }: { company: Company }) {
  return (
    <span
      className={`inline-block min-w-[2rem] text-center rounded px-1.5 py-0.5 text-xs font-semibold tabular-nums ${scoreStyle(company.icp_score)}`}
    >
      {company.icp_score}
    </span>
  )
}
