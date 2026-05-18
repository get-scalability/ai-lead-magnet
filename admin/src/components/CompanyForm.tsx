import { type FormEvent, useRef, useState } from 'react'

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

const GENERIC_PROVIDERS = new Set([
  'gmail.com', 'googlemail.com',
  'outlook.com', 'outlook.fr', 'hotmail.com', 'hotmail.fr', 'hotmail.co.uk',
  'live.com', 'live.fr', 'msn.com',
  'yahoo.com', 'yahoo.fr', 'yahoo.co.uk',
  'orange.fr', 'wanadoo.fr', 'sfr.fr', 'free.fr', 'laposte.net',
  'icloud.com', 'me.com', 'mac.com',
  'aol.com', 'protonmail.com', 'proton.me',
])

function extractDomain(email: string): string | null {
  const at = email.lastIndexOf('@')
  if (at === -1) return null
  const domain = email.slice(at + 1).toLowerCase()
  return GENERIC_PROVIDERS.has(domain) ? null : domain
}

export function CompanyForm({ onSubmit, phase }: CompanyFormProps) {
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [domain, setDomain] = useState('')
  const [icpPrompt, setIcpPrompt] = useState('')
  const domainAutoFilled = useRef(false)

  function handleEmailChange(value: string) {
    setEmail(value)
    const extracted = extractDomain(value)
    if (extracted && (domain === '' || domainAutoFilled.current)) {
      setDomain(extracted)
      domainAutoFilled.current = true
    } else if (!extracted && domainAutoFilled.current) {
      setDomain('')
      domainAutoFilled.current = false
    }
  }

  function handleDomainChange(value: string) {
    domainAutoFilled.current = false
    setDomain(value)
  }

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
            onChange={(e) => handleEmailChange(e.target.value)}
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
          onChange={(e) => handleDomainChange(e.target.value)}
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
