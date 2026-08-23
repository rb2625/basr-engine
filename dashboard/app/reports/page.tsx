"use client";

import Reveal from "@/components/Reveal";
import Section from "@/components/Section";
import FreshnessBar from "@/components/FreshnessBar";
import { useApi } from "@/components/useApi";
import type { ReportItem, ReportsData } from "@/lib/types";

const KIND_STYLE: Record<ReportItem["kind"], string> = {
  daily: "bg-accent/10 text-accent border-accent/30",
  weekly: "bg-vio/15 text-vio border-vio/40",
  org: "bg-pos/15 text-pos border-pos/40",
};

const DELIVERY_DOT: Record<string, string> = {
  pending: "bg-accent",
  sent: "bg-pos",
  failed: "bg-neg",
  skipped: "bg-neu",
};

function fmtDate(d: string | null): string {
  if (!d) return "";
  return d.slice(0, 10);
}

function sent(v: number | null | undefined): string {
  if (v == null) return "n/a";
  return v.toFixed(2);
}

export default function ReportsPage() {
  const { data, error, loading, refreshing, lastUpdated, refresh } = useApi<ReportsData>("reports", "", 120000);
  return (
    <div className="space-y-6">
      <div className="mb-7 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-accent">
          Agents / scheduled reports
        </div>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-text1 sm:text-3xl">
          UAE Pulse
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mute">
          The daily UAE Pulse and weekly sector digest are auto-generated from
          the measured time series and delivered over the same channels as
          alerts. Every number in a report traces to the database - no vibes.
        </p>
      </div>
        <FreshnessBar lastUpdated={lastUpdated} onRefresh={refresh} refreshing={refreshing} />

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
      ) : data.reports.length === 0 ? (
        <div className="card p-10 text-center font-mono text-xs text-mute">
          No reports yet - the cron generates the daily UAE Pulse on every
          run and the weekly digest once per week.
        </div>
      ) : (
        <Reveal delay={100}>
          <Section
            kicker="Report archive"
            title="Generated digests"
            right={
              <span className="font-mono text-[11px] text-mute">
                measured, not vibes
              </span>
            }
          >
            <ul className="divide-y divide-line">
              {data.reports.map((r) => (
                <li key={r.id} className="py-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-md border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide ${KIND_STYLE[r.kind]}`}
                    >
                      {r.kind}
                    </span>
                    <span className="text-[15px] font-semibold text-text1">
                      {r.title}
                    </span>
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[11px] text-mute">
                    {r.periodStart && r.periodEnd && (
                      <span className="tabular-nums">
                        {fmtDate(r.periodStart)} to {fmtDate(r.periodEnd)}
                      </span>
                    )}
                    <span className="inline-flex items-center gap-1.5">
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${DELIVERY_DOT[r.deliveryStatus] || "bg-neu"}`}
                      />
                      {r.deliveryStatus}
                      {r.channel ? ` / ${r.channel}` : ""}
                    </span>
                  </div>

                  {r.narrative && (
                    <p className="mt-3 max-w-3xl text-[13px] leading-relaxed text-text1">
                      {r.narrative}
                    </p>
                  )}

                  {r.headlines.length > 0 && (
                    <ul className="mt-2.5 space-y-1">
                      {r.headlines.map((h, i) => (
                        <li
                          key={i}
                          className="flex gap-2 text-[12.5px] text-mute"
                        >
                          <span className="font-mono text-[11px] text-accent">
                            &gt;
                          </span>
                          {h}
                        </li>
                      ))}
                    </ul>
                  )}

                  {(r.stats.top_topics?.length || r.stats.top_emirates?.length) && (
                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      {r.stats.top_topics && r.stats.top_topics.length > 0 && (
                        <div className="rounded-lg border border-line bg-panel-2/50 p-3">
                          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-mute">
                            Top topics
                          </div>
                          <ul className="mt-2 space-y-1 text-[12px]">
                            {r.stats.top_topics.slice(0, 5).map((t, i) => (
                              <li key={i} className="flex justify-between gap-2">
                                <span className="text-text1">{t.topic}</span>
                                <span className="font-mono text-mute">
                                  {t.volume}
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {r.stats.top_emirates && r.stats.top_emirates.length > 0 && (
                        <div className="rounded-lg border border-line bg-panel-2/50 p-3">
                          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-mute">
                            Top emirates
                          </div>
                          <ul className="mt-2 space-y-1 text-[12px]">
                            {r.stats.top_emirates.slice(0, 5).map((e, i) => (
                              <li key={i} className="flex justify-between gap-2">
                                <span className="text-text1">{e.emirate}</span>
                                <span className="font-mono text-mute">
                                  {e.volume}
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-mute">
                    <span>
                      volume {r.stats.current_volume ?? "n/a"}
                      {r.stats.volume_delta_pct != null && (
                        <span className="text-accent">
                          {" "}
                          ({r.stats.volume_delta_pct > 0 ? "+" : ""}
                          {r.stats.volume_delta_pct}% vs prior)
                        </span>
                      )}
                    </span>
                    <span>sentiment {sent(r.stats.sentiment_avg)}</span>
                    {r.stats.open_alerts != null && (
                      <span>{r.stats.open_alerts} open alerts</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </Section>
        </Reveal>
      )}
    </div>
  );
}
