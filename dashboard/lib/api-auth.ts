import { NextRequest } from "next/server";
import { createClient } from "@supabase/supabase-js";

const API_KEYS = (process.env.BASR_API_KEYS || "").split(",").filter(Boolean);

export function validateApiKey(request: NextRequest): { valid: boolean; key?: string; error?: string } {
  const authHeader = request.headers.get("authorization");
  if (!authHeader?.startsWith("Bearer ")) {
    return { valid: false, error: "Missing Authorization header. Use: Authorization: Bearer <api_key>" };
  }
  const key = authHeader.slice(7).trim();
  if (!key) {
    return { valid: false, error: "Empty API key" };
  }
  // In development, accept any key. In production, check against list.
  if (API_KEYS.length > 0 && !API_KEYS.includes(key)) {
    return { valid: false, error: "Invalid API key" };
  }
  return { valid: true, key };
}

export function getSupabase() {
  return createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}
