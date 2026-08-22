"use client";

import { SentimentSeries } from "@/components/Charts";
import KpiCard from "@/components/KpiCard";
import MixBar from "@/components/MixBar";
import Reveal from "@/components/Reveal";
import Section from "@/components/Section";
import FreshnessBar from "@/components/FreshnessBar";
import { SignalBadge, SentimentBadge } from "@/components/Badge";
import { useApi } from "@/components/useApi";
import type { OverviewData } from "@/lib/types";

export default function OverviewPage() {
  const { data, error, loading, lastUpdated, refresh } =
    useApi<OverviewData>("overview", "", 120000);

  if (loading) {
    return (
      <div className="space-y-5">
        <div>
          <h1 className="font-display-xl glow-text">UAE Market Pulse</h1>
          <p className="mt-1 font-body-lg text-ink-3">
            Real-time sentiment intelligence.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="card p-4">
              <div className="skeleton h-2.5 w-14" />
              <div className="skeleton mt-3 h-6 w-20" />
              <div className="skeleton mt-2 h-2.5 w-24" />
            </div>
          ))}
        </div>
        <div className="card p-4">
          <div className="skeleton h-52 w-full" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-5">
        <div>
          <h1 className="font-display-xl glow-text">UAE Market Pulse</h1>
          <p className="mt-1 font-body-lg text-ink-3">
            Real-time sentiment intelligence.
          </p>
        </div>
        <div className="card max-w-md border-rose/20 bg-rose/5 p-4 text-body-sm text-rose">
          <div className="font-semibold">Could not load data</div>
          <div className="mt-1 break-all font-mono text-[10px] opacity-70">
            {error || "No data"}
          </div>
          <button
            onClick={refresh}
            className="mt-3 rounded-lg bg-rose/10 px-3 py-1.5 text-[11px] font-medium text-rose transition-colors hover:bg-rose/20"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const maxTopic = Math.max(1, ...data.topTopics.map((t) => t.docs));

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-display-xl glow-text">UAE Market Pulse</h1>
          <p className="mt-1 font-body-lg text-ink-3">
            Public sentiment across housing, jobs, prices, and more.
          </p>
        </div>
        <FreshnessBar lastUpdated={lastUpdated} onRefresh={refresh} />
      </div>

      <Reveal>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {data.kpis.map((k, i) => (
            <KpiCard
              key={k.label}
              label={k.label}
              value={k.value}
              sub={k.sub}
              delay={60 * i}
            />
          ))}
        </div>
      </Reveal>

      <div className="grid gap-3 lg:grid-cols-5">
        <Reveal delay={80} className="lg:col-span-2">
          <Section kicker="Classification" title="Signal mix">
            <MixBar mix={data.mix} />
          </Section>
        </Reveal>

        <Reveal delay={120} className="lg:col-span-3">
          <Section kicker="Topics" title="Coverage by topic">
            <div className="space-y-2.5">
              {data.topTopics.map((t, i) => {
                const colors = [
                  "#818CF8",
                  "#C084FC",
                  "#FBBF24",
                  "#34D399",
                  "#22D3EE",
                  "#FB7185",
                  "#F472B6",
                  "#A78BFA",
                ];
                const c = colors[i % colors.length];
                return (
                  <div key={t.key} className="group flex items-center gap-3">
                    <div className="w-32 shrink-0 truncate text-[11px] font-medium text-ink-2">
                      {t.labelEn}
                    </div>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.04]">
                      <div
                        className="bar-grow h-full rounded-full"
                        style={{
                          width: `${(100 * t.docs) / maxTopic}%`,
                          backgroundColor: c,
                        }}
                      />
                    </div>
                    <div className="w-7 text-right font-mono text-[9px] tabular-nums text-ink-3">
                      {t.docs}
                    </div>
                    <div
                      className={
                        "w-12 text-right font-mono text-[9px] tabular-nums font-medium " +
                        (t.avgSentiment == null
                          ? "text-ink-3"
                          : t.avgSentiment >= 0.15
                            ? "text-positive"
                            : t.avgSentiment <= -0.15
                              ? "text-negative"
                              : "text-neutral")
                      }
                    >
                      {t.avgSentiment == null ? "n/a" : t.avgSentiment.toFixed(2)}
                    </div>
                  </div>
                );
              })}
            </div>
          </Section>
        </Reveal>
      </div>

      <Reveal delay={100}>
        <Section kicker="Trends" title="Volume and sentiment (30 days)">
          <SentimentSeries series={data.series} />
        </Section>
      </Reveal>

      <Reveal delay={140}>
        <Section kicker="Early warning" title="Recent stress signals">
          {data.recentStress.length === 0 ? (
            <div className="font-mono text-[10px] text-ink-3">
              No stress signals yet
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              {data.recentStress.map((f) => (
                <div
                  key={f.id}
                  className="group flex items-start justify-between gap-3 py-3 transition-colors hover:bg-white/[0.02] -mx-3 px-3 rounded-xl"
                >
                  <div className="min-w-0">
                    <div className="text-[12px] font-medium text-ink truncate">
                      {f.title}
                      {f.locations.length > 0 && (
                        <span className="ml-1.5 font-mono text-[9px] font-normal text-ink-3">
                          {f.locations.join(", ")}
                        </span>
                      )}
                    </div>
                    <div className="mt-0.5 font-mono text-[9px] text-ink-3">
                      {f.source} /{" "}
                      {f.published_at ? f.published_at.slice(0, 10) : "unknown"}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    <SignalBadge signal={f.signal_type} />
                    <SentimentBadge label={f.sentiment_label} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>
      </Reveal>
    </div>
  );
}
