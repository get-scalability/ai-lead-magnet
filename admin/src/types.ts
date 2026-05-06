export type AppPhase = 'done' | 'error' | 'idle' | 'loading'

export type Company = {
  country: string
  domain: string | null
  icp_score: number
  industry: string
  linkedin_url: string | null
  name: string
  size: string
}

export type RunResult = {
  broaden_suggestions: string[]
  companies: Company[]
  total_found: number
}

export type StatusMessage = {
  detail?: string
  message: string
}
