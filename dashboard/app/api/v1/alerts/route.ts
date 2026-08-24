import { NextRequest, NextResponse } from "next/server";
import { validateApiKey, getSupabase } from "@/lib/api-auth";

export async function GET(request: NextRequest) {
  const auth = validateApiKey(request);
  if (!auth.valid) {
    return NextResponse.json({ error: auth.error }, { status: 401 });
  }

  const sb = getSupabase();
  const limit = Math.min(parseInt(request.nextUrl.searchParams.get("limit") || "20", 10), 100);

  const { data, error } = await sb
    .from("alerts")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({
    count: data?.length || 0,
    data: data || [],
  });
}
