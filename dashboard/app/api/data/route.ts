import { NextRequest, NextResponse } from "next/server";
import {
  buildAlerts,
  buildBriefs,
  buildFeedback,
  buildFeed,
  buildMap,
  buildOverview,
  buildReports,
  buildTopics,
  buildTrends,
} from "@/lib/aggregate";

// Always fetch fresh data - this is a live intelligence dashboard.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const view = request.nextUrl.searchParams.get("view") || "overview";
  const limitRaw = Number(request.nextUrl.searchParams.get("limit") || 30);
  const limit = Number.isFinite(limitRaw) ? Math.min(100, Math.max(5, limitRaw)) : 30;
  try {
    switch (view) {
      case "map":
        return NextResponse.json(await buildMap());
      case "trends":
        return NextResponse.json(await buildTrends());
      case "topics":
        return NextResponse.json(await buildTopics());
      case "feed":
        return NextResponse.json(await buildFeed(limit));
      case "alerts":
        return NextResponse.json(await buildAlerts());
      case "briefs":
        return NextResponse.json(await buildBriefs());
      case "reports":
        return NextResponse.json(await buildReports());
      case "feedback":
        return NextResponse.json(await buildFeedback());
      case "overview":
      default:
        return NextResponse.json(await buildOverview());
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { error: message },
      { status: 500, headers: { "Cache-Control": "no-store" } }
    );
  }
}
