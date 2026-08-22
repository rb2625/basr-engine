"use client";

import { SentimentSeries, StressStack } from "@/components/Charts";
import Reveal from "@/components/Reveal";
import Section from "@/components/Section";
import FreshnessBar from "@/components/FreshnessBar";
import { useApi } from "@/components/useApi";
import type { TrendsData } from "@/lib/types";

export default function TrendsPage() {
  const { data, error, loading, lastUpdated, refresh } = useApi<TrendsData>("trends", "", 120000);
  return (
    <div className="space-y-6">
      <div className="mb-7 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-accent">
          Time series / momentum
        </div>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-text1 sm:text-3xl">
          Sentiment trends
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mute">
          Daily volume, average sentiment, and stress signals by topic over the
          last 30 days.
        </p>
      </div>
        <FreshnessBar lastUpdated={lastUpdated} onRefresh={refresh} />

      {loading ? (
        <div className="space-y-6">
          <div className="card p-6">
            <div className="skeleton h-64 w-full rounded" />
          </div>
          <div className="card p-6">
            <div className="skeleton h-64 w-full rounded" />
          </div>
        </div>
      ) : error || !data ? (
        <div className="card max-w-xl border-neg/30 p-6 text-sm text-neg">
          {error || "No data"}
        </div>
      ) : (
        <>
          <Reveal>
            <Section kicker="Volume / sentiment" title="Daily volume and average sentiment">
              <SentimentSeries series={data.series} />
            </Section>
          </Reveal>
          <Reveal delay={120}>
            <Section
              kicker="Topic breakdown"
              title="Stress signals per day, by top topics"
            >
              <StressStack series={data.series} topics={data.topTopicKeys} />
            </Section>
          </Reveal>
        </>
      )}
    </div>
  );
}
