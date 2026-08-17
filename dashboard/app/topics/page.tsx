"use client";

import MixBar from "@/components/MixBar";
import { useApi } from "@/components/useApi";
import type { TopicsData } from "@/lib/types";

export default function TopicsPage() {
  const { data, error, loading } = useApi<TopicsData>("topics");
  if (loading) {
    return <div className="py-16 text-center text-zinc-400">Loading topics...</div>;
  }
  if (error || !data) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        {error || "No data"}
      </div>
    );
  }
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Topics</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Every doc is tagged with up to 3 topics by the zero-token keyword layer.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {data.topics.map((t) => (
          <div key={t.key} className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
            <div className="flex items-baseline justify-between">
              <h3 className="font-semibold text-zinc-800">{t.labelEn}</h3>
              <span className="text-xs text-zinc-400">{t.docs} docs</span>
            </div>
            <div className="mt-1 text-xs text-zinc-500">
              Avg sentiment:{" "}
              <span
                className={
                  "font-semibold " +
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
              </span>
            </div>
            <div className="mt-3">
              <MixBar mix={t.mix} />
            </div>
            {t.latest && (
              <div className="mt-2 text-[11px] text-zinc-400">
                Latest: {t.latest.slice(0, 10)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
