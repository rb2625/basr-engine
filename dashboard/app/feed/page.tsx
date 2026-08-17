"use client";

import Reveal from "@/components/Reveal";
import Section from "@/components/Section";
import { SignalBadge, SentimentBadge } from "@/components/Badge";
import { useApi } from "@/components/useApi";
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
  return (
    <div className="space-y-6">
      <div className="mb-7">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-gold">
          Stream / classified docs
        </div>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-text1 sm:text-3xl">
          Classified feed
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mute">
          Latest docs with their sentiment, signal, sector, and topic tags.
        </p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="card p-5">
              <div className="skeleton h-4 w-3/4 rounded" />
              <div className="skeleton mt-3 h-3 w-1/3 rounded" />
            </div>
          ))}
        </div>
      ) : error || !data ? (
        <div className="card max-w-xl border-neg/30 p-6 text-sm text-neg">
          {error || "No data"}
        </div>
      ) : (
        <Reveal>
          <Section
            kicker="Stream"
            title="Latest classified docs"
            right={
              <span className="font-mono text-[11px] tabular-nums text-mute">
                {data.totalClassified} classified in corpus
              </span>
            }
          >
            {data.items.length === 0 ? (
              <div className="py-8 text-center font-mono text-xs text-mute">
                No classified docs yet - the NLP pipeline is warming up.
              </div>
            ) : (
              <ul className="divide-y divide-line">
                {data.items.map((f) => (
                  <li key={f.id} className="py-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-text1">{f.title}</div>
                        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[11px] text-mute">
                          <span className="uppercase tracking-wide">{f.source}</span>
                          <span className="tabular-nums">{timeAgo(f.published_at)}</span>
                          {f.sector && (
                            <span className="text-golddim">{f.sector}</span>
                          )}
                          {f.sarcasm && (
                            <span className="font-semibold text-vio">sarcasm</span>
                          )}
                        </div>
                        {(f.topics.length > 0 || f.locations.length > 0) && (
                          <div className="mt-2.5 flex flex-wrap gap-1.5">
                            {f.topics.map((t) => (
                              <span
                                key={t}
                                className="rounded-md border border-line bg-panel2 px-1.5 py-0.5 font-mono text-[10px] text-mute"
                              >
                                {t}
                              </span>
                            ))}
                            {f.locations.map((l) => (
                              <span
                                key={l}
                                className="rounded-md border border-gold/25 bg-gold/10 px-1.5 py-0.5 font-mono text-[10px] capitalize text-gold"
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
                    <div className="mt-2 font-mono text-[10px] text-mute">
                      {f.model_version} / conf{" "}
                      {f.confidence == null ? "n/a" : f.confidence.toFixed(2)}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Section>
        </Reveal>
      )}
    </div>
  );
}
