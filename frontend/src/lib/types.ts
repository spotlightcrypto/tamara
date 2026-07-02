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
export type Confidence = 'low' | 'medium' | 'high'

export interface ProposalCompany {
  ticker: string
  exchange: string
  name?: string | null
  reason?: string | null
}

export interface ProposalItem {
  kind: ItemKind
  body: string
  event_date?: string | null
  cite?: string | null
}

export interface Proposal {
  title: string
  thesis: string
  companies: ProposalCompany[]
  items: ProposalItem[]
  confidence: Confidence
  open_questions: string[]
}

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
