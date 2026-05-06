import type { AppPhase, StatusMessage } from '../types'

type StatusLogProps = {
  error: string | null
  messages: StatusMessage[]
  phase: AppPhase
}

function Spinner() {
  return (
    <div
      aria-label="Loading"
      className="w-4 h-4 rounded-full border-2 border-ag-border border-t-ag-blue animate-spin flex-shrink-0"
      role="status"
    />
  )
}

export function StatusLog({ error, messages, phase }: StatusLogProps) {
  if (phase === 'idle') return null

  return (
    <div className="mt-6 space-y-1">
      {messages.map((msg, i) => (
        <div key={i} className="flex items-start gap-2">
          <span className="mt-0.5 text-ag-text-muted">·</span>
          <div>
            <span className="text-sm text-ag-text-secondary">{msg.message}</span>
            {msg.detail && (
              <span className="ml-2 text-xs text-ag-text-muted">{msg.detail}</span>
            )}
          </div>
        </div>
      ))}

      {phase === 'loading' && (
        <div className="flex items-center gap-2 pt-1">
          <Spinner />
          <span className="text-sm text-ag-text-muted italic">Processing…</span>
        </div>
      )}

      {phase === 'error' && error && (
        <div className="mt-3 flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <span className="text-ag-red font-medium text-sm">{error}</span>
        </div>
      )}
    </div>
  )
}
