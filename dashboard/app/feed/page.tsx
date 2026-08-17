"use client";

import { useApi } from "@/components/useApi";
import { SignalBadge, SentimentBadge } from "@/components/Badge";
import type { FeedData } from "@/lib/types";

function timeAgo(ts: string | null): string {
  if (!ts) return "unknown";
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function FeedPage() {
  const { data, error, loading } = useApi<FeedData>("feed", "&limit=50");
  if (loading) {
    return <div className="py-16 text-center text-zinc-400">Loading feed...</div>;
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
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-xl font-bold">Latest classified docs</h1>
          <p className="mt-1 text-sm text-zinc-500">
            {data.totalClassified} classified docs in the corpus.
          </p>
        </div>
      </div>
      {data.items.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white p-8 text-center text-sm text-zinc-400">
          No classified docs yet - the NLP pipeline is still warming up.
        </div>
      ) : (
        <ul className="divide-y divide-zinc-100 rounded-xl border border-zinc-200 bg-white shadow-sm">
          {data.items.map((f) => (
            <li key={f.id} className="px-5 py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-zinc-800">{f.title}</div>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-400">
                    <span>{f.source}</span>
                    <span>{timeAgo(f.published_at)}</span>
                    {f.sector && <span>Sector: {f.sector}</span>}
                    {f.sarcasm && <span className="font-semibold text-violet-500">sarcasm</span>}
                  </div>
                  {(f.topics.length > 0 || f.locations.length > 0) && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {f.topics.map((t) => (
                        <span
                          key={t}
                          className="rounded bg-zinc-100 px-1.5 py-0.5 text-[11px] text-zinc-600"
                        >
                          {t}
                        </span>
                      ))}
                      {f.locations.map((l) => (
                        <span
                          key={l}
                          className="rounded bg-amber-50 px-1.5 py-0.5 text-[11px] text-amber-700"
                        >
                          {l}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <SignalBadge signal={f.signal_type} />
                  <SentimentBadge label={f.sentiment_label} />
                </div>
              </div>
              <div className="mt-2 text-[11px] text-zinc-300">
                {f.model_version} - conf {f.confidence == null ? "n/a" : f.confidence.toFixed(2)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
