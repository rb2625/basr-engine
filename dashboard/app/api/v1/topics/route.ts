import { NextRequest, NextResponse } from "next/server";
import { validateApiKey, getSupabase } from "@/lib/api-auth";

export async function GET(request: NextRequest) {
  const auth = validateApiKey(request);
  if (!auth.valid) {
    return NextResponse.json({ error: auth.error }, { status: 401 });
  }

  const sb = getSupabase();

  const { data, error } = await sb
    .from("classifications")
    .select("sector, sentiment_label, sentiment_score")
    .not("sector", "eq", "General")
    .order("created_at", { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // Aggregate by sector
  const sectors: Record<string, { count: number; positive: number; negative: number; neutral: number; avgScore: number }> = {};
  for (const row of data || []) {
    const s = row.sector || "General";
    if (!sectors[s]) sectors[s] = { count: 0, positive: 0, negative: 0, neutral: 0, avgScore: 0 };
    sectors[s].count++;
    if (row.sentiment_label === "positive") sectors[s].positive++;
    else if (row.sentiment_label === "negative") sectors[s].negative++;
    else sectors[s].neutral++;
    sectors[s].avgScore += row.sentiment_score || 0;
  }

  for (const s of Object.values(sectors)) {
    s.avgScore = Math.round((s.avgScore / s.count) * 1000) / 1000;
  }

  return NextResponse.json({
    count: data?.length || 0,
    sectors,
  });
}
