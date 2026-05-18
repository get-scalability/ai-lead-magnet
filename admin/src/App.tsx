import { CompanyForm } from './components/CompanyForm'
import { ResultsTable } from './components/ResultsTable'
import { StatusLog } from './components/StatusLog'
import { useCompanyList } from './hooks/useCompanyList'

function Header() {
  return (
    <div className="mb-8">
      <p className="text-xs font-semibold text-ag-blue uppercase tracking-widest mb-3">
        Scalability · AI Tools
      </p>
      <h1 className="text-2xl font-semibold text-ag-text-primary mb-2">
        Build your target company list
      </h1>
      <p className="text-sm text-ag-text-secondary max-w-lg">
        Describe your ideal customers and get an AI-curated list of matching companies —
        scored, enriched, and ready for outbound.
      </p>
    </div>
  )
}

export function App() {
  const { error, phase, publicId, rateLimitResetOn, result, run, statusMessages } = useCompanyList()

  return (
    <div className="min-h-screen bg-ag-bg-primary px-4 py-12">
      <div className="max-w-3xl mx-auto">
        <Header />

        <div className="bg-white border border-ag-border rounded-xl p-6 shadow-sm">
          <CompanyForm onSubmit={run} phase={phase} />
        </div>

        <StatusLog
          error={error}
          messages={statusMessages}
          phase={phase}
          rateLimitResetOn={rateLimitResetOn}
        />

        {result && (
          <ResultsTable publicId={publicId} result={result} />
        )}
      </div>
    </div>
  )
}
