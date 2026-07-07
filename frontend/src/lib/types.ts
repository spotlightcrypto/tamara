// Shapes returned by / sent to the backend API. Mirror app/models on the server.

export interface Narrative {
  id: string
  title: string
  thesis: string
  body_md: string
  positioning: string | null
  is_active: boolean
  is_public: boolean
  author_username: string | null
  created_at: string
  updated_at: string
}

// The caller's own identity (the only place an email is returned, to its owner).
export interface Me {
  user_id: string
  email: string | null
  username: string | null
}

export interface UsernameCheck {
  available: boolean
  reason?: string | null
}

export interface Profile {
  id: string
  username: string
  created_at: string
  updated_at: string
}

export interface Note {
  id: string
  narrative_id: string
  body: string
  created_at: string
  updated_at: string
}

export interface PricePerformance {
  ticker: string
  as_of: string | null
  price?: number | null // latest close (current price)
  performance: Record<string, number> // e.g. { "1D": -2.05, "1W": 12.5, ... }
  since_date?: string | null
  since_close?: number | null
  since_change?: number | null
}

export interface Source {
  id: string
  narrative_id: string
  url: string
  title: string // short "few words" display name
  created_at: string
}

export interface Company {
  id: string
  ticker: string
  exchange: string // friendly display name, "NASDAQ"
  mic: string // ISO 10383 canonical code, "XNAS" — the identity key
  currency: string | null
  country: string | null
  tier: number | null // 1 US, 2 major-developed (priced), 3 narrative-only (no price)
  symbol: string // friendly derived "TICKER:EXCHANGE"
  slug: string // canonical URL identity "ticker:mic" (lowercased)
  name: string
  sector: string | null
  profile: Record<string, unknown> | null
  fundamentals: Record<string, unknown> | null
  last_hydrated_at: string | null
  created_at: string
  updated_at: string
}

// A narrative plus the companies attached to it. The backend embeds these in
// list responses (GET /narratives, GET /companies/:id/narratives) in one query.
export interface NarrativeWithCompanies extends Narrative {
  companies: Company[]
}

// A listing found via the external symbol resolver but not (yet) in our DB — no
// `id`. Enough to render a chip and start the first narrative for it.
export interface ResolvedListing {
  ticker: string
  mic: string
  exchange: string
  name: string
  currency: string | null
  tier: number | null
  has_price: boolean
  symbol: string // derived "TICKER:EXCHANGE"
  slug: string // canonical "ticker:mic" (lowercased)
}

// Combined local search: the caller's narratives + globally-known companies.
export interface SearchResults {
  narratives: NarrativeWithCompanies[]
  companies: Company[]
}

// --- Guided intake (kernel -> questionnaire -> proposal) ---

export interface QuestionOption {
  label: string
  description?: string | null
}

export interface Question {
  id: string
  header: string
  question: string
  options: QuestionOption[]
  multi_select: boolean
  allow_free_text: boolean
  open_ended: boolean // render as a free-response textarea, no options
}

export interface Answer {
  question_id: string
  selected: string[]
  free_text?: string | null
  skipped?: boolean
}

export interface ProposalCompany {
  ticker: string
  exchange: string
  name?: string | null
  reason?: string | null
}

export interface Proposal {
  title: string
  thesis: string
  positioning: string
  companies: ProposalCompany[]
  suggested_companies: ProposalCompany[]
  body_md: string
}

export const MAX_COMPANIES = 8
export const POSITIONING_LABELS = [
  'megabull',
  'permabull',
  'normiebull',
  'megabear',
  'ultrabear',
] as const

export interface KernelSummary {
  kind: string
  title?: string | null
  excerpt?: string | null
}

export interface IntakeState {
  draft_id: string
  status: string
  kernel: KernelSummary
  round: number
  questions?: Question[] | null
  proposal?: Proposal | null
}
