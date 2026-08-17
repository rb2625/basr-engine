"use client";

import { SentimentSeries, StressStack } from "@/components/Charts";
import { useApi } from "@/components/useApi";
import type { TrendsData } from "@/lib/types";

export default function TrendsPage() {
  const { data, error, loading } = useApi<TrendsData>("trends");
  if (loading) {
    return <div className="py-16 text-center text-zinc-400">Loading trends...</div>;
  }
  if (error || !data) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        {error || "No data"}
      </div>
    );
  }
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">Sentiment trends</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Daily volume, average sentiment, and stress signals by topic over the last 30 days.
        </p>
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-zinc-700">
          Daily volume and average sentiment
        </h2>
        <SentimentSeries series={data.series} />
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-zinc-700">
          Stress signals per day, broken down by top topics
        </h2>
        <StressStack series={data.series} topics={data.topTopicKeys} />
      </div>
    </div>
  );
}
