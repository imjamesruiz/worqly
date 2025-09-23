import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

// Debug logging
console.log("Environment variables loaded:")
console.log("VITE_SUPABASE_URL:", supabaseUrl ? "✓ Set" : "✗ Not set")
console.log("VITE_SUPABASE_ANON_KEY:", supabaseAnonKey ? "✓ Set" : "✗ Not set")

// Use placeholder values if environment variables are not set
const url = supabaseUrl || 'https://placeholder.supabase.co'
const key = supabaseAnonKey || 'placeholder-anon-key'

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn("Supabase environment variables are not set. Using placeholder values. Authentication will not work properly.")
  console.warn("To fix this, create a .env file in the frontend directory with:")
  console.warn("VITE_SUPABASE_URL=https://your-project-id.supabase.co")
  console.warn("VITE_SUPABASE_ANON_KEY=your-anon-key-here")
} else {
  console.log("✓ Supabase configuration loaded successfully")
  console.log("URL:", url)
}

export const supabase = createClient(url, key, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})

export async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? null
}


