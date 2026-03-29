import type {
  ChemistryMetrics,
  SessionResponse,
  SpectrumResponse,
  XicResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const NORMALIZED_API_BASE = API_BASE.replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${NORMALIZED_API_BASE}${path}`, init)
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message =
      payload && typeof payload === 'object' && 'detail' in payload
        ? String(payload.detail)
        : `Request failed with status ${response.status}`
    throw new Error(message)
  }
  return payload as T
}

export async function uploadDataset(file: File): Promise<SessionResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return request<SessionResponse>('/api/uploads', {
    method: 'POST',
    body: formData,
  })
}

export function createDemoSession(): Promise<SessionResponse> {
  return request<SessionResponse>('/api/demo', {
    method: 'POST',
  })
}

export function fetchSpectrum(sessionId: string, rt: number): Promise<SpectrumResponse> {
  const params = new URLSearchParams({ rt: rt.toString() })
  return request<SpectrumResponse>(`/api/sessions/${sessionId}/spectrum?${params.toString()}`)
}

export function fetchXic(sessionId: string, mz: number, ppm: number): Promise<XicResponse> {
  const params = new URLSearchParams({ mz: mz.toString(), ppm: ppm.toString() })
  return request<XicResponse>(`/api/sessions/${sessionId}/xic?${params.toString()}`)
}

export function calculateChemistryMetrics(payload: {
  neutralMass: number
  charge: number
  observedMz?: number
}): Promise<ChemistryMetrics> {
  return request<ChemistryMetrics>('/api/chemistry/metrics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      neutral_mass: payload.neutralMass,
      charge: payload.charge,
      observed_mz: payload.observedMz,
    }),
  })
}
