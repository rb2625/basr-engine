"use client";

import { SentimentSeries } from "@/components/Charts";
import KpiCard from "@/components/KpiCard";
import MixBar from "@/components/MixBar";
import { SignalBadge, SentimentBadge } from "@/components/Badge";
import { useApi } from "@/components/useApi";
import type { OverviewData } from "@/lib/types";

export default function OverviewPage() {
  const { data, error, loading } = useApi<OverviewData>("overview");

  if (loading) {
    return <div className="py-16 text-center text-zinc-400">Loading live intelligence...</div>;
  }
  if (error || !data) {
    return (
      <div className="mx-auto max-w-xl rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        <div className="font-semibold">Could not load data</div>
        <div className="mt-1 break-all">{error || "No data returned"}</div>
        <div className="mt-3 text-xs text-red-600">
          Server-side: check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the
          dashboard environment. See dashboard/.env.local.example.
        </div>
      </div>
    );
  }

  const maxTopic = Math.max(1, ...data.topTopics.map((t) => t.docs));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {data.kpis.map((k) => (
          <KpiCard key={k.label} label={k.label} value={k.value} sub={k.sub} />
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold text-zinc-700">
            Signal mix - all classified docs
          </h2>
          <MixBar mix={data.mix} />
        </div>
        <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm lg:col-span-3">
          <h2 className="mb-3 text-sm font-semibold text-zinc-700">
            Top topics by volume
          </h2>
          <div className="space-y-2.5">
            {data.topTopics.map((t) => (
              <div key={t.key} className="flex items-center gap-3">
                <div className="w-36 shrink-0 truncate text-sm text-zinc-700">
                  {t.labelEn}
                </div>
                <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-zinc-100">
                  <div
                    className="h-full rounded-full bg-amber-400"
                    style={{ width: `${(100 * t.docs) / maxTopic}%` }}
                  />
                </div>
                <div className="w-8 text-right text-xs text-zinc-500">{t.docs}</div>
                <div
                  className={
                    "w-14 text-right text-xs font-medium " +
                    (t.avgSentiment == null
                      ? "text-zinc-400"
                      : t.avgSentiment >= 0.15
                        ? "text-emerald-600"
                        : t.avgSentiment <= -0.15
                          ? "text-red-600"
                          : "text-amber-600")
                  }
                >
                  {t.avgSentiment == null ? "n/a" : t.avgSentiment.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-zinc-700">
          Last 30 days - volume and sentiment
        </h2>
        <SentimentSeries series={data.series} />
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-zinc-700">
          Recent stress signals
        </h2>
        {data.recentStress.length === 0 ? (
          <div className="text-sm text-zinc-400">No stress signals classified yet</div>
        ) : (
          <ul className="divide-y divide-zinc-100">
            {data.recentStress.map((f) => (
              <li key={f.id} className="flex items-start justify-between gap-4 py-3">
                <div>
                  <div className="text-sm font-medium text-zinc-800">
                    {f.title}
                    {f.locations.length > 0 && (
                      <span className="ml-2 text-xs font-normal text-zinc-400">
                        {f.locations.join(", ")}
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 text-xs text-zinc-400">
                    {f.source} - {f.published_at ? f.published_at.slice(0, 10) : "unknown"}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <SignalBadge signal={f.signal_type} />
                  <SentimentBadge label={f.sentiment_label} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
