import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { IcpScoreBadge } from '../components/IcpScoreBadge'
import type { BroadenSuggestion, Company, RunResult } from '../types'

type ResultData = {
  created_at: string
  input: { domain: string; icp_prompt: string }
  output: RunResult
  public_id: string
}

type PageState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'loaded'; data: ResultData }

const VISIBLE_ROWS = 10

const thClass =
  'text-left text-xs font-medium text-ag-text-muted uppercase tracking-wide px-4 py-3'

function CompanyRow({ company }: { company: Company }) {
  return (
    <tr className="border-b border-ag-border last:border-0">
      <td className="px-4 py-3 w-16">
        <IcpScoreBadge company={company} />
      </td>
      <td className="px-4 py-3 font-medium text-sm text-ag-text-primary">
        {company.linkedin_url ? (
          <a
            className="text-ag-blue hover:underline"
            href={company.linkedin_url}
            rel="noopener noreferrer"
            target="_blank"
          >
            {company.name}
          </a>
        ) : (
          company.name
        )}
      </td>
      <td className="px-4 py-3 text-sm text-ag-text-secondary">
        {company.domain ? (
          <a
            className="text-ag-blue hover:underline"
            href={`https://${company.domain}`}
            rel="noopener noreferrer"
            target="_blank"
          >
            {company.domain}
          </a>
        ) : (
          <span className="text-ag-text-muted">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-ag-text-secondary">
        {company.industry || <span className="text-ag-text-muted">—</span>}
      </td>
      <td className="px-4 py-3 text-sm text-ag-text-secondary whitespace-nowrap">
        {company.size || <span className="text-ag-text-muted">—</span>}
      </td>
      <td className="px-4 py-3 text-sm text-ag-text-secondary">
        {company.country || <span className="text-ag-text-muted">—</span>}
      </td>
    </tr>
  )
}

function BlurGate({ hidden }: { hidden: Company[] }) {
  return (
    <div className="relative border border-t-0 border-ag-border rounded-b-lg overflow-hidden">
      <table className="w-full text-sm border-collapse pointer-events-none select-none">
        <tbody className="[filter:blur(3px)]">
          {hidden.slice(0, 4).map((company, i) => (
            <CompanyRow key={i} company={company} />
          ))}
        </tbody>
      </table>
      <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-white/95 flex flex-col items-center justify-end pb-8 pt-4">
        <p className="text-sm font-semibold text-ag-text-primary">
          {hidden.length} more companies hidden
        </p>
        <p className="text-xs text-ag-text-secondary mt-1 mb-5">
          Run your own search to unlock all results
        </p>
        <Link
          className="bg-ag-text-primary text-ag-bg-primary font-semibold text-sm px-5 py-2.5 rounded-lg
            hover:bg-ag-text-secondary transition-colors"
          to="/"
        >
          Build my list →
        </Link>
      </div>
    </div>
  )
}

function ResultView({ data }: { data: ResultData }) {
  const companies = data.output.companies
  const visible = companies.slice(0, VISIBLE_ROWS)
  const hidden = companies.slice(VISIBLE_ROWS)
  const createdAt = new Date(data.created_at).toLocaleDateString('en', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return (
    <div className="min-h-screen bg-ag-bg-primary px-4 py-12">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <p className="text-xs font-semibold text-ag-blue uppercase tracking-widest mb-3">
            Scalability · AI Tools
          </p>
          <h1 className="text-2xl font-semibold text-ag-text-primary mb-1">
            Company list for {data.input.domain}
          </h1>
          <p className="text-sm text-ag-text-secondary">
            {companies.length} companies found · Generated {createdAt}
          </p>
        </div>

        {data.output.broaden_suggestions.length > 0 && (
          <div className="mb-4 p-3 bg-ag-bg-secondary border border-ag-border rounded-lg text-xs text-ag-text-secondary">
            <p className="font-medium mb-2">💡 Broaden results</p>
            <div className="flex flex-wrap gap-2">
              {data.output.broaden_suggestions.map((s: BroadenSuggestion, i: number) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 border border-ag-border rounded-md px-2.5 py-1 bg-white"
                >
                  <span className="text-ag-text-primary">{s.label}</span>
                  <span className="text-ag-text-muted">{s.hint}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        <div className={`border border-ag-border overflow-hidden ${hidden.length > 0 ? 'rounded-t-lg' : 'rounded-lg'}`}>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-ag-bg-secondary border-b border-ag-border">
                <th className={`${thClass} w-16`}>ICP</th>
                <th className={thClass}>Company</th>
                <th className={thClass}>Domain</th>
                <th className={thClass}>Industry</th>
                <th className={thClass}>Size</th>
                <th className={thClass}>Country</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((company, i) => (
                <CompanyRow key={i} company={company} />
              ))}
            </tbody>
          </table>
        </div>

        {hidden.length > 0 && <BlurGate hidden={hidden} />}

        <div className="mt-8 p-4 bg-white border border-ag-border rounded-xl text-center">
          <p className="text-sm font-medium text-ag-text-primary mb-1">
            Want a list tailored to your ICP?
          </p>
          <p className="text-xs text-ag-text-secondary mb-4">
            This is someone else&apos;s result. Run your own search for free.
          </p>
          <Link
            className="inline-block bg-ag-text-primary text-ag-bg-primary font-semibold text-sm
              px-5 py-2.5 rounded-lg hover:bg-ag-text-secondary transition-colors"
            to="/"
          >
            Build my list →
          </Link>
        </div>
      </div>
    </div>
  )
}

export function ResultPage() {
  const { publicId } = useParams<{ publicId: string }>()
  const [state, setState] = useState<PageState>({ status: 'loading' })

  useEffect(() => {
    if (!publicId) {
      setState({ status: 'error', message: 'Invalid result link.' })
      return
    }
    fetch(`/agents/company-list/result/${publicId}`)
      .then((r) => {
        if (r.status === 404) throw new Error('This result has expired or doesn't exist.')
        if (!r.ok) throw new Error('Failed to load result.')
        return r.json() as Promise<ResultData>
      })
      .then((data) => setState({ status: 'loaded', data }))
      .catch((err: Error) => setState({ status: 'error', message: err.message }))
  }, [publicId])

  if (state.status === 'loading') {
    return (
      <div className="min-h-screen bg-ag-bg-primary flex items-center justify-center">
        <div className="w-6 h-6 rounded-full border-2 border-ag-border border-t-ag-blue animate-spin" />
      </div>
    )
  }

  if (state.status === 'error') {
    return (
      <div className="min-h-screen bg-ag-bg-primary flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-sm text-ag-text-secondary text-center">{state.message}</p>
        <Link
          className="text-sm font-medium text-ag-blue hover:underline"
          to="/"
        >
          ← Build your own list
        </Link>
      </div>
    )
  }

  return <ResultView data={state.data} />
}
