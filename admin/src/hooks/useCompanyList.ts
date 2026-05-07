import { useCallback, useState } from 'react'

import type { AppPhase, RunResult, StatusMessage } from '../types'

export type UseCompanyListReturn = {
  error: string | null
  phase: AppPhase
  publicId: string | null
  rateLimitResetOn: string | null
  result: RunResult | null
  run: (email: string, firstName: string | null, domain: string, icpPrompt: string) => Promise<void>
  statusMessages: StatusMessage[]
}

type SseCallbacks = {
  onDone: (publicId: string) => void
  onError: (message: string) => void
  onRateLimit: (resetOn: string) => void
  onResult: (result: RunResult) => void
  onStatus: (message: StatusMessage) => void
}

type RunRequest = {
  domain: string
  email: string
  first_name: string | null
  icp_prompt: string
}

const SSE_EVENT_PREFIX = 'event: '
const SSE_DATA_PREFIX = 'data: '
const HTTP_RATE_LIMIT = 429

function getStr(obj: Record<string, unknown>, key: string): string {
  const val = obj[key]
  return typeof val === 'string' ? val : ''
}

function handleSseEvent(type: string, raw: string, callbacks: SseCallbacks): void {
  let parsed: Record<string, unknown>
  try {
    const p = JSON.parse(raw) as unknown
    if (typeof p !== 'object' || p === null) return
    parsed = p as Record<string, unknown>
  } catch {
    return
  }

  if (type === 'status') {
    const detail = getStr(parsed, 'detail')
    callbacks.onStatus({ detail: detail || undefined, message: getStr(parsed, 'message') })
  } else if (type === 'result') {
    callbacks.onResult(parsed as unknown as RunResult)
  } else if (type === 'done') {
    callbacks.onDone(getStr(parsed, 'public_id'))
  } else if (type === 'error') {
    callbacks.onError(getStr(parsed, 'message') || 'An unexpected error occurred.')
  }
}

async function readStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onEvent: (type: string, data: string) => void,
): Promise<void> {
  const decoder = new TextDecoder()
  let buffer = ''
  let eventType = ''
  let chunk = await reader.read()

  while (!chunk.done) {
    buffer += decoder.decode(chunk.value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (line.startsWith(SSE_EVENT_PREFIX)) {
        eventType = line.slice(SSE_EVENT_PREFIX.length).trim()
      } else if (line.startsWith(SSE_DATA_PREFIX)) {
        onEvent(eventType, line.slice(SSE_DATA_PREFIX.length).trim())
        eventType = ''
      }
    }

    chunk = await reader.read()
  }
}

async function streamRun(req: RunRequest, callbacks: SseCallbacks): Promise<void> {
  let response: Response
  try {
    response = await fetch('/agents/company-list/stream', {
      body: JSON.stringify(req),
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
    })
  } catch (err) {
    callbacks.onError(err instanceof Error ? err.message : 'Network error')
    return
  }

  if (response.status === HTTP_RATE_LIMIT) {
    let resetOn = 'next month'
    try {
      const body = await response.json() as { detail?: { reset_on?: string } }
      if (body?.detail?.reset_on) resetOn = body.detail.reset_on
    } catch { /* ignore */ }
    callbacks.onRateLimit(resetOn)
    return
  }

  if (!response.ok || !response.body) {
    callbacks.onError(`Server error (${response.status.toString()})`)
    return
  }

  const reader = response.body.getReader()
  await readStream(reader, (type, data) => handleSseEvent(type, data, callbacks))
}

export function useCompanyList(): UseCompanyListReturn {
  const [phase, setPhase] = useState<AppPhase>('idle')
  const [statusMessages, setStatusMessages] = useState<StatusMessage[]>([])
  const [result, setResult] = useState<RunResult | null>(null)
  const [publicId, setPublicId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [rateLimitResetOn, setRateLimitResetOn] = useState<string | null>(null)

  const run = useCallback(
    async (email: string, firstName: string | null, domain: string, icpPrompt: string) => {
      setPhase('loading')
      setStatusMessages([])
      setResult(null)
      setPublicId(null)
      setError(null)
      setRateLimitResetOn(null)

      await streamRun(
        { domain, email, first_name: firstName, icp_prompt: icpPrompt },
        {
          onDone: (id) => { setPublicId(id); setPhase('done') },
          onError: (msg) => { setError(msg); setPhase('error') },
          onRateLimit: (resetOn) => { setRateLimitResetOn(resetOn); setPhase('rate_limited') },
          onResult: setResult,
          onStatus: (msg) => setStatusMessages((prev) => [...prev, msg]),
        },
      )

      setPhase((prev) => (prev === 'loading' ? 'done' : prev))
    },
    [],
  )

  return { error, phase, publicId, rateLimitResetOn, result, run, statusMessages }
}
