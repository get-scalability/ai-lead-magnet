export type AppPhase = 'done' | 'error' | 'idle' | 'loading' | 'rate_limited'

export type RunParams = {
  domain: string
  email: string
  firstName: string | null
  icpPrompt: string
}

export type Company = {
  country: string
  domain: string | null
  icp_score: number
  industry: string
  linkedin_url: string | null
  name: string
  size: string
}

export type BroadenSuggestion = {
  hint: string
  label: string
}

export type RunResult = {
  broaden_suggestions: BroadenSuggestion[]
  companies: Company[]
  total_found: number
}

export type StatusMessage = {
  detail?: string
  message: string
}
