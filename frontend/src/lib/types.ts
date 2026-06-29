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
