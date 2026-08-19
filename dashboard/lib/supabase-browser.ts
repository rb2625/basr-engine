"use client";

import { createClient, SupabaseClient } from "@supabase/supabase-js";

let _client: SupabaseClient | null = null;

export function getBrowserClient(): SupabaseClient | null {
  if (_client) return _client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey || anonKey === "YOUR_ANON_KEY_HERE") {
    // Auth not configured. Dashboard still works for data viewing.
    return null;
  }
  _client = createClient(url, anonKey);
  return _client;
}
