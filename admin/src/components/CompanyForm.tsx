import { type FormEvent, useState } from 'react'

import type { AppPhase } from '../types'

type CompanyFormProps = {
  onSubmit: (email: string, firstName: string | null, domain: string, icpPrompt: string) => void
  phase: AppPhase
}

const inputClass =
  'w-full bg-white border border-ag-border rounded-lg px-3 py-2 text-sm text-ag-text-primary ' +
  'placeholder:text-ag-text-muted focus:outline-none focus:border-ag-blue transition-colors ' +
  'disabled:opacity-50 disabled:cursor-not-allowed'

const labelClass = 'block text-xs font-medium text-ag-text-secondary uppercase tracking-wide mb-1.5'

export function CompanyForm({ onSubmit, phase }: CompanyFormProps) {
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [domain, setDomain] = useState('')
  const [icpPrompt, setIcpPrompt] = useState('')

  const isLoading = phase === 'loading'
  const canSubmit =
    email.trim().length > 0 &&
    domain.trim().length > 0 &&
    icpPrompt.trim().length > 0 &&
    !isLoading

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!canSubmit) return
    onSubmit(email.trim(), firstName.trim() || null, domain.trim(), icpPrompt.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>Your email</label>
          <input
            className={inputClass}
            disabled={isLoading}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            required
            type="email"
            value={email}
          />
        </div>
        <div>
          <label className={labelClass}>
            First name{' '}
            <span className="font-normal normal-case text-ag-text-muted">(optional)</span>
          </label>
          <input
            className={inputClass}
            disabled={isLoading}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Alex"
            type="text"
            value={firstName}
          />
        </div>
      </div>

      <div>
        <label className={labelClass}>Your company domain</label>
        <input
          className={inputClass}
          disabled={isLoading}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="company.com"
          required
          type="text"
          value={domain}
        />
      </div>

      <div>
        <label className={labelClass}>Describe your ideal target companies</label>
        <textarea
          className={`${inputClass} resize-none`}
          disabled={isLoading}
          onChange={(e) => setIcpPrompt(e.target.value)}
          placeholder="e.g. B2B SaaS companies in France, 50–500 employees, using outbound sales…"
          required
          rows={4}
          value={icpPrompt}
        />
        <p className="mt-1 text-xs text-ag-text-muted">
          Be specific: industry, size, geography, tech stack, sales motion…
        </p>
      </div>

      <button
        className="w-full bg-ag-text-primary text-ag-bg-primary font-semibold text-sm py-2.5 rounded-lg
          hover:bg-ag-text-secondary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        disabled={!canSubmit}
        type="submit"
      >
        {isLoading ? 'Building your list…' : 'Build my list →'}
      </button>

      <p className="text-xs text-center text-ag-text-muted">
        By getting your results, you&apos;ll occasionally hear from Scalability.{' '}
        <a
          className="underline hover:text-ag-text-secondary transition-colors"
          href="https://getscalability.io/unsubscribe"
          rel="noopener noreferrer"
          target="_blank"
        >
          Unsubscribe anytime
        </a>
        {' · '}
        <a
          className="underline hover:text-ag-text-secondary transition-colors"
          href="https://getscalability.io/privacy"
          rel="noopener noreferrer"
          target="_blank"
        >
          Privacy policy
        </a>
      </p>
    </form>
  )
}
