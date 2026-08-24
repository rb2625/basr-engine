import { NextRequest, NextResponse } from "next/server";
import { validateApiKey, getSupabase } from "@/lib/api-auth";

export async function GET(request: NextRequest) {
  const auth = validateApiKey(request);
  if (!auth.valid) {
    return NextResponse.json({ error: auth.error }, { status: 401 });
  }

  const sb = getSupabase();
  const { searchParams } = request.nextUrl;
  const sector = searchParams.get("sector");
  // source filter: uncomment when raw_docs join is added
  const days = parseInt(searchParams.get("days") || "7", 10);
  const limit = Math.min(parseInt(searchParams.get("limit") || "50", 10), 200);

  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);

  let query = sb
    .from("classifications")
    .select("id, raw_doc_id, sentiment_score, sentiment_label, emotion, signal_type, sector, intensity_score, confidence, created_at")
    .gte("created_at", cutoff.toISOString())
    .order("created_at", { ascending: false })
    .limit(limit);

  if (sector) query = query.eq("sector", sector);

  const { data, error } = await query;
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({
    count: data?.length || 0,
    sector: sector || "all",
    days,
    data: data || [],
  });
}
