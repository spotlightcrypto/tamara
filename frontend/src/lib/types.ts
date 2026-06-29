// Shapes returned by / sent to the backend API. Mirror app/models on the server.

export interface Narrative {
  id: string
  title: string
  thesis: string
  created_at: string
  updated_at: string
}

export interface NarrativeCreate {
  title: string
  thesis?: string
}

export interface Company {
  id: string
  ticker: string
  exchange: string
  symbol: string // derived "TICKER:EXCHANGE"
  name: string
  sector: string | null
  profile: Record<string, unknown> | null
  fundamentals: Record<string, unknown> | null
  last_hydrated_at: string | null
  created_at: string
  updated_at: string
}

// A narrative plus the companies attached to it (composed client-side for now).
export interface NarrativeWithCompanies extends Narrative {
  companies: Company[]
}
