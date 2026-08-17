import { createClient, SupabaseClient } from "@supabase/supabase-js";

// Server-side only. The service-role key never reaches the browser: every
// page/component reads through /api/data, which runs with these env vars.
let _client: SupabaseClient | null = null;

export function getClient(): SupabaseClient {
  if (_client) return _client;
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error(
      "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set (see .env.local.example)"
    );
  }
  _client = createClient(url, key);
  return _client;
}
