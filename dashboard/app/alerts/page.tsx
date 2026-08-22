"use client";

import Reveal from "@/components/Reveal";
import Section from "@/components/Section";
import FreshnessBar from "@/components/FreshnessBar";
import { useApi } from "@/components/useApi";
import type { AlertsData, AlertItem } from "@/lib/types";

const SEV_STYLE: Record<AlertItem["severity"], string> = {
  critical: "bg-neg/15 text-neg border-neg/40",
  high: "bg-orange-400/15 text-orange-300 border-orange-400/40",
  medium: "bg-accent/10 text-accent border-accent/30",
  low: "bg-neu/20 text-mute border-line",
};

const STATUS_DOT: Record<string, string> = {
  open: "bg-pos",
  acknowledged: "bg-accent",
  dismissed: "bg-neu",
  promoted: "bg-vio",
};

function timeAgo(ts: string | null): string {
  if (!ts) return "unknown";
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function AlertsPage() {
  const { data, error, loading, lastUpdated, refresh } = useApi<AlertsData>("alerts", "", 120000);
  return (
    <div className="space-y-6">
      <div className="mb-7 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-accent">
          Early warning / anomalies
        </div>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-text1 sm:text-3xl">
          Anomaly alerts
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mute">
          Volume spikes detected by the BASR ensemble (rolling z-score + STL
          seasonality) on the daily time series. A spike is flagged only when
          it clears a volume floor and a deviation threshold - a single noisy
          day is never an alert.
        </p>
      </div>
        <FreshnessBar lastUpdated={lastUpdated} onRefresh={refresh} />

      {loading ? (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card p-5">
              <div className="skeleton h-4 w-2/3 rounded" />
              <div className="skeleton mt-3 h-3 w-1/3 rounded" />
            </div>
          ))}
        </div>
      ) : error || !data ? (
        <div className="card max-w-xl border-neg/30 p-6 text-sm text-neg">
          {error || "No data"}
        </div>
      ) : data.alerts.length === 0 ? (
        <div className="card p-10 text-center font-mono text-xs text-mute">
          No anomalies flagged yet - the ensemble needs at least 15 days of
          history before it trusts a baseline.
        </div>
      ) : (
        <>
          <Reveal>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
              <div className="card p-4">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-mute">
                  Total alerts
                </div>
                <div className="mt-1 font-mono text-2xl font-semibold text-text1">
                  {data.alerts.length}
                </div>
              </div>
              <div className="card p-4">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-mute">
                  Open
                </div>
                <div className="mt-1 font-mono text-2xl font-semibold text-pos">
                  {data.open}
                </div>
              </div>
              <div className="card p-4">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-mute">
                  Critical
                </div>
                <div className="mt-1 font-mono text-2xl font-semibold text-neg">
                  {data.critical}
                </div>
              </div>
            </div>
          </Reveal>

          <Reveal delay={100}>
            <Section
              kicker="Detection log"
              title="Flagged spikes"
              right={
                <span className="font-mono text-[11px] text-mute">
                  ensemble z + STL
                </span>
              }
            >
              <ul className="divide-y divide-line">
                {data.alerts.map((a) => (
                  <li key={a.id} className="py-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`rounded-md border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide ${SEV_STYLE[a.severity]}`}
                          >
                            {a.severity}
                          </span>
                          <span className="text-[15px] font-semibold text-text1">
                            {a.title}
                          </span>
                        </div>
                        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[11px] text-mute">
                          {a.bucketStart && (
                            <span className="tabular-nums">{a.bucketStart.slice(0, 10)}</span>
                          )}
                          <span className="inline-flex items-center gap-1.5">
                            <span
                              className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[a.status] || "bg-neu"}`}
                            />
                            {a.status}
                          </span>
                          <span className="tabular-nums">{timeAgo(a.createdAt)}</span>
                        </div>
                      </div>
                    </div>
                    {a.evidence.length > 0 && (
                      <ul className="mt-2.5 space-y-1 border-l border-line pl-3">
                        {a.evidence.map((e) => (
                          <li key={e.id} className="text-[12px] text-mute">
                            <span className="text-text1">{e.title}</span>
                            <span className="ml-2 font-mono text-[10.5px] uppercase">
                              {e.source}
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </Section>
          </Reveal>
        </>
      )}
    </div>
  );
}
