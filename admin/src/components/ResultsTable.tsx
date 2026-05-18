import { IcpScoreBadge } from './IcpScoreBadge'

import type { BroadenSuggestion, Company, RunResult } from '../types'

type ResultsTableProps = {
  publicId: string | null
  result: RunResult
}

const CSV_ENDPOINT = '/agents/company-list/result'

function CompanyName({ company }: { company: Company }) {
  if (company.linkedin_url) {
    return (
      <a
        className="text-ag-blue hover:underline"
        href={company.linkedin_url}
        rel="noopener noreferrer"
        target="_blank"
      >
        {company.name}
      </a>
    )
  }
  return <span>{company.name}</span>
}

function CompanyDomain({ company }: { company: Company }) {
  if (!company.domain) return <span className="text-ag-text-muted">—</span>
  return (
    <a
      className="text-ag-blue hover:underline"
      href={`https://${company.domain}`}
      rel="noopener noreferrer"
      target="_blank"
    >
      {company.domain}
    </a>
  )
}

function EmptyCell({ value }: { value: string }) {
  if (value) return <span>{value}</span>
  return <span className="text-ag-text-muted">—</span>
}

export function ResultsTable({ publicId, result }: ResultsTableProps) {
  const csvUrl = publicId ? `${CSV_ENDPOINT}/${publicId}/csv` : null
  const permalinkUrl = publicId ? `/r/${publicId}` : null

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-ag-text-primary">
            {result.total_found} companies found
          </h2>
          {permalinkUrl && (
            <a
              className="text-xs text-ag-text-muted hover:text-ag-blue transition-colors"
              href={permalinkUrl}
              rel="noopener noreferrer"
              target="_blank"
            >
              Permanent link to these results ↗
            </a>
          )}
        </div>
        {csvUrl && (
          <a
            className="flex items-center gap-1.5 text-xs font-medium text-ag-text-secondary border border-ag-border
              rounded-lg px-3 py-1.5 hover:border-ag-blue hover:text-ag-blue transition-colors"
            href={csvUrl}
          >
            ↓ Download CSV
          </a>
        )}
      </div>

      {result.broaden_suggestions.length > 0 && (
        <div className="mb-4 p-3 bg-ag-bg-secondary border border-ag-border rounded-lg text-xs text-ag-text-secondary">
          <p className="font-medium mb-2">💡 Want more results?</p>
          <div className="flex flex-wrap gap-2">
            {result.broaden_suggestions.map((s: BroadenSuggestion, i: number) => (
              <span key={i} className="inline-flex items-center gap-1.5 border border-ag-border rounded-md px-2.5 py-1 bg-white">
                <span className="text-ag-text-primary">{s.label}</span>
                <span className="text-ag-text-muted">{s.hint}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="border border-ag-border rounded-lg overflow-hidden">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-ag-bg-secondary border-b border-ag-border">
              <th className="text-left text-xs font-medium text-ag-text-muted uppercase tracking-wide px-4 py-3 w-16">
                ICP
              </th>
              <th className="text-left text-xs font-medium text-ag-text-muted uppercase tracking-wide px-4 py-3">
                Company
              </th>
              <th className="text-left text-xs font-medium text-ag-text-muted uppercase tracking-wide px-4 py-3">
                Domain
              </th>
              <th className="text-left text-xs font-medium text-ag-text-muted uppercase tracking-wide px-4 py-3">
                Industry
              </th>
              <th className="text-left text-xs font-medium text-ag-text-muted uppercase tracking-wide px-4 py-3">
                Size
              </th>
              <th className="text-left text-xs font-medium text-ag-text-muted uppercase tracking-wide px-4 py-3">
                Country
              </th>
            </tr>
          </thead>
          <tbody>
            {result.companies.map((company, i) => (
              <tr
                key={i}
                className="border-b border-ag-border last:border-0 hover:bg-ag-bg-secondary transition-colors"
              >
                <td className="px-4 py-3">
                  <IcpScoreBadge company={company} />
                </td>
                <td className="px-4 py-3 font-medium">
                  <CompanyName company={company} />
                </td>
                <td className="px-4 py-3 text-ag-text-secondary">
                  <CompanyDomain company={company} />
                </td>
                <td className="px-4 py-3 text-ag-text-secondary">
                  <EmptyCell value={company.industry} />
                </td>
                <td className="px-4 py-3 text-ag-text-secondary whitespace-nowrap">
                  <EmptyCell value={company.size} />
                </td>
                <td className="px-4 py-3 text-ag-text-secondary">
                  <EmptyCell value={company.country} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
