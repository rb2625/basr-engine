"use client";

import { SentimentSeries } from "@/components/Charts";
import KpiCard from "@/components/KpiCard";
import MixBar from "@/components/MixBar";
import Reveal from "@/components/Reveal";
import Section from "@/components/Section";
import { SignalBadge, SentimentBadge } from "@/components/Badge";
import { useApi } from "@/components/useApi";
import type { OverviewData } from "@/lib/types";

function PageHeader() {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight text-text1 sm:text-3xl">
        UAE Market Pulse
      </h1>
      <p className="mt-1.5 max-w-2xl text-sm text-mute">
        Public sentiment across housing, jobs, prices, and more. Classified by the BASR hybrid model.
      </p>
    </div>
  );
}

function Loading() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="card p-5">
            <div className="skeleton h-3 w-16" />
            <div className="skeleton mt-3 h-7 w-24" />
            <div className="skeleton mt-2 h-3 w-28" />
          </div>
        ))}
      </div>
      <div className="card p-6">
        <div className="skeleton h-64 w-full" />
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const { data, error, loading } = useApi<OverviewData>("overview");

  if (loading) {
    return (
      <div>
        <PageHeader />
        <Loading />
      </div>
    );
  }
  if (error || !data) {
    return (
      <div>
        <PageHeader />
        <div className="card max-w-xl border-neg/30 bg-neg-light p-6 text-sm text-neg">
          <div className="font-semibold">Could not load data</div>
          <div className="mt-1 break-all font-mono text-xs opacity-70">{error || "No data returned"}</div>
        </div>
      </div>
    );
  }

  const maxTopic = Math.max(1, ...data.topTopics.map((t) => t.docs));

  return (
    <div className="space-y-6">
      <PageHeader />

      <Reveal>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {data.kpis.map((k, i) => (
            <KpiCard
              key={k.label}
              label={k.label}
              value={k.value}
              sub={k.sub}
              tooltip={
                k.label === "Total docs"
                  ? "Raw documents ingested from all 5 sources"
                  : k.label === "Classified"
                  ? "Documents with sentiment + signal labels"
                  : k.label === "Topics"
                  ? "14 UAE-specific topic categories"
                  : k.label === "Alerts"
                  ? "Active anomaly alerts requiring attention"
                  : undefined
              }
              delay={60 * i}
            />
          ))}
        </div>
      </Reveal>

      <div className="grid gap-6 lg:grid-cols-5">
        <Reveal delay={90} className="lg:col-span-2">
          <Section
            kicker="Classification"
            title="Signal mix"
            delay={90}
          >
            <MixBar mix={data.mix} />
          </Section>
        </Reveal>

        <Reveal delay={160} className="lg:col-span-3">
          <Section kicker="Topics" title="Coverage by topic" delay={160}>
            <div className="space-y-2.5">
              {data.topTopics.map((t) => (
                <div key={t.key} className="group flex items-center gap-3">
                  <div className="w-36 shrink-0 truncate text-[13px] text-text1">
                    {t.labelEn}
                  </div>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-panel2">
                    <div
                      className="bar-grow h-full rounded-full bg-accent"
                      style={{ width: `${(100 * t.docs) / maxTopic}%` }}
                    />
                  </div>
                  <div className="w-8 text-right font-mono text-xs tabular-nums text-mute">
                    {t.docs}
                  </div>
                  <div
                    className={
                      "w-14 text-right font-mono text-xs tabular-nums " +
                      (t.avgSentiment == null
                        ? "text-mute"
                        : t.avgSentiment >= 0.15
                          ? "text-pos"
                          : t.avgSentiment <= -0.15
                            ? "text-neg"
                            : "text-neu")
                    }
                  >
                    {t.avgSentiment == null ? "n/a" : t.avgSentiment.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </Section>
        </Reveal>
      </div>

      <Reveal delay={120}>
        <Section kicker="Trends" title="Volume and sentiment (30 days)">
          <SentimentSeries series={data.series} />
        </Section>
      </Reveal>

      <Reveal delay={180}>
        <Section kicker="Early warning" title="Recent stress signals">
          {data.recentStress.length === 0 ? (
            <div className="font-mono text-xs text-mute">No stress signals classified yet</div>
          ) : (
            <ul className="divide-y divide-line">
              {data.recentStress.map((f) => (
                <li key={f.id} className="group flex items-start justify-between gap-4 py-3">
                  <div>
                    <div className="text-sm font-medium text-text1">
                      {f.title}
                      {f.locations.length > 0 && (
                        <span className="ml-2 font-mono text-[11px] font-normal text-mute">
                          {f.locations.join(", ")}
                        </span>
                      )}
                    </div>
                    <div className="mt-0.5 font-mono text-[11px] text-mute">
                      {f.source} / {f.published_at ? f.published_at.slice(0, 10) : "unknown"}
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
        </Section>
      </Reveal>
    </div>
  );
}
