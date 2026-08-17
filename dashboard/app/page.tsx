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
    <div className="mb-7">
      <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-gold">
        Signal room / overview
      </div>
      <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-text1 sm:text-3xl">
        UAE market pulse
      </h1>
      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mute">
        Aggregated public sentiment across housing, jobs, prices, and more -
        classified by the BASR hybrid model, scored on a 500-item eval set.
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
            <div className="skeleton h-3 w-16 rounded" />
            <div className="skeleton mt-3 h-8 w-24 rounded" />
            <div className="skeleton mt-2 h-3 w-28 rounded" />
          </div>
        ))}
      </div>
      <div className="card p-6">
        <div className="skeleton h-64 w-full rounded" />
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
        <div className="card max-w-xl border-neg/30 p-6 text-sm text-neg">
          <div className="font-semibold">Could not load data</div>
          <div className="mt-1 break-all font-mono text-xs">{error || "No data returned"}</div>
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
              delay={60 * i}
            />
          ))}
        </div>
      </Reveal>

      <div className="grid gap-6 lg:grid-cols-5">
        <Reveal delay={90} className="lg:col-span-2">
          <Section
            kicker="Classification"
            title="Signal mix - all classified docs"
            delay={90}
          >
            <MixBar mix={data.mix} />
          </Section>
        </Reveal>

        <Reveal delay={160} className="lg:col-span-3">
          <Section kicker="Volume" title="Top topics by coverage" delay={160}>
            <div className="space-y-3">
              {data.topTopics.map((t) => (
                <div key={t.key} className="group flex items-center gap-3">
                  <div className="w-40 shrink-0 truncate text-[13px] text-text1">
                    {t.labelEn}
                  </div>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-ink/60 ring-1 ring-line">
                    <div
                      className="bar-grow h-full rounded-full bg-gradient-to-r from-golddim to-gold"
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
                            : "text-gold")
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
        <Section kicker="30-day window" title="Volume and average sentiment">
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
                <li key={f.id} className="group flex items-start justify-between gap-4 py-3.5">
                  <div>
                    <div className="text-sm font-medium text-text1">
                      {f.title}
                      {f.locations.length > 0 && (
                        <span className="ml-2 font-mono text-[11px] font-normal text-mute">
                          {f.locations.join(", ")}
                        </span>
                      )}
                    </div>
                    <div className="mt-1 font-mono text-[11px] text-mute">
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
