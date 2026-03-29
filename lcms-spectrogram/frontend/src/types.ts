export type SessionStatus = 'uploaded' | 'ready' | 'conversion_error' | 'parse_error'

export interface DatasetSummary {
  scanCount: number
  rtMin: number
  rtMax: number
  mzMin: number
  mzMax: number
  intensityMax: number
  sourceName: string
  sourceKind: string
  approximateMassRange: [number, number]
}

export interface TracePoint {
  rt: number
  intensity: number
}

export interface HeatmapPoint {
  rt: number
  mz: number
  intensity: number
}

export interface SessionResponse {
  sessionId: string
  status: SessionStatus
  message: string
  filename: string
  sourceKind: string
  notes: string[]
  datasetNotes?: string[]
  summary?: DatasetSummary
  tic?: TracePoint[]
  heatmapPoints?: HeatmapPoint[]
}

export interface SpectrumPeakLabel {
  mz: number
  intensity: number
}

export interface SpectrumResponse {
  scanId: string
  rt: number
  msLevel: number
  mz: number[]
  intensity: number[]
  peakLabels: SpectrumPeakLabel[]
}

export interface XicResponse {
  targetMz: number
  ppmTolerance: number
  trace: TracePoint[]
}

export interface ChemistryMetrics {
  theoreticalMz: number
  ppmError: number | null
  isotopeSpacing: number
}
