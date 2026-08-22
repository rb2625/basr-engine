"use client";

import Reveal from "@/components/Reveal";
import Section from "@/components/Section";
import { useApi } from "@/components/useApi";
import type { BriefItem, BriefsData } from "@/lib/types";

const SEV_STYLE: Record<BriefItem["severity"], string> = {
  critical: "bg-neg/15 text-neg border-neg/40",
  high: "bg-orange-400/15 text-orange-300 border-orange-400/40",
  medium: "bg-accent/10 text-accent border-accent/30",
  low: "bg-neu/20 text-mute border-line",
};

const STATUS_DOT: Record<string, string> = {
  draft: "bg-neu",
  published: "bg-pos",
  delivered: "bg-vio",
  archived: "bg-neu",
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

export default function BriefsPage() {
  const { data, error, loading } = useApi<BriefsData>("briefs");
  return (
    <div className="space-y-6">
      <div className="mb-7">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-accent">
          Agents / decision support
        </div>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-text1 sm:text-3xl">
          Intelligence briefs
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mute">
          An alert promoted by an analyst becomes a decision-ready brief:
          what/where/who, sentiment trajectory, top evidence with links,
          severity (impact x urgency x spread), and ordered recommended
          responses for the owning organization.
        </p>
      </div>

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
      ) : data.briefs.length === 0 ? (
        <div className="card p-10 text-center font-mono text-xs text-mute">
          No briefs yet - promote an open alert from the early warning view
          and it appears here as a published brief.
        </div>
      ) : (
        <>
          <Reveal>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
              <div className="card p-4">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-mute">
                  Total briefs
                </div>
                <div className="mt-1 font-mono text-2xl font-semibold text-text1">
                  {data.briefs.length}
                </div>
              </div>
              <div className="card p-4">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-mute">
                  Published
                </div>
                <div className="mt-1 font-mono text-2xl font-semibold text-pos">
                  {data.published}
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
              kicker="Brief library"
              title="Decision-ready analysis"
              right={
                <span className="font-mono text-[11px] text-mute">
                  severity = impact x urgency x spread
                </span>
              }
            >
              <ul className="divide-y divide-line">
                {data.briefs.map((b) => (
                  <li key={b.id} className="py-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`rounded-md border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide ${SEV_STYLE[b.severity]}`}
                          >
                            {b.severity}
                          </span>
                          <span className="text-[15px] font-semibold text-text1">
                            {b.title}
                          </span>
                        </div>
                        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[11px] text-mute">
                          <span className="inline-flex items-center gap-1.5">
                            <span
                              className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[b.status] || "bg-neu"}`}
                            />
                            {b.status}
                          </span>
                          <span className="tabular-nums">{timeAgo(b.createdAt)}</span>
                          <span className="text-[10px] uppercase">
                            {b.modelVersion}
                          </span>
                        </div>
                      </div>
                    </div>

                    <p className="mt-3 max-w-3xl text-[13px] leading-relaxed text-mute">
                      {b.summary}
                    </p>

                    {b.recommendedResponse.length > 0 && (
                      <div className="mt-3 space-y-1.5">
                        {b.recommendedResponse.map((r, i) => (
                          <div
                            key={i}
                            className="flex gap-2.5 border-l border-gold/30 pl-3 text-[12.5px]"
                          >
                            <span className="font-mono text-[11px] text-accent">
                              {String(i + 1).padStart(2, "0")}
                            </span>
                            <div className="min-w-0">
                              <span className="text-text1">{r.action}</span>
                              <span className="text-mute">
                                {" "}
                                - {r.owner}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {b.evidence.length > 0 && (
                      <div className="mt-3 rounded-lg border border-line bg-panel-2/50 p-3">
                        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-mute">
                          Evidence
                        </div>
                        <ul className="mt-2 space-y-1">
                          {b.evidence
                            .filter((e) => e.title)
                            .slice(0, 4)
                            .map((e, i) => (
                              <li key={i} className="flex flex-wrap items-baseline gap-x-2 text-[12px]">
                                {e.url ? (
                                  <a
                                    href={e.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-text1 underline decoration-line underline-offset-2 hover:text-accent"
                                  >
                                    {e.title}
                                  </a>
                                ) : (
                                  <span className="text-text1">{e.title}</span>
                                )}
                                {e.source && (
                                  <span className="font-mono text-[10.5px] uppercase text-mute">
                                    {e.source}
                                  </span>
                                )}
                              </li>
                            ))}
                        </ul>
                        {b.evidence.some((e) => e.severity_justification) && (
                          <p className="mt-2 border-t border-line pt-2 text-[11.5px] italic leading-relaxed text-mute">
                            {b.evidence.find((e) => e.severity_justification)
                              ?.severity_justification}
                          </p>
                        )}
                      </div>
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
