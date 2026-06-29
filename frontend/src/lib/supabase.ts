import { createClient } from '@supabase/supabase-js'

// The browser's Supabase client — used only for Auth (login/session). All data
// access goes through our backend API, never directly to Supabase from here.
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
)
