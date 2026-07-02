// Shapes returned by / sent to the backend API. Mirror app/models on the server.

export interface Narrative {
  id: string
  title: string
  thesis: string
  body_md: string
  positioning: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface NarrativeCreate {
  title: string
  thesis?: string
}

export interface Item {
  id: string
  narrative_id: string
  kind: 'bull' | 'bear' | 'catalyst' | 'risk'
  body: string
  event_date: string | null
  position: number
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

// A narrative plus the companies attached to it. The backend embeds these in
// list responses (GET /narratives, GET /companies/:id/narratives) in one query.
export interface NarrativeWithCompanies extends Narrative {
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
}

export interface Answer {
  question_id: string
  selected: string[]
  free_text?: string | null
  skipped?: boolean
}

export type ItemKind = 'bull' | 'bear' | 'catalyst' | 'risk'

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
