"use client";

import MixBar from "@/components/MixBar";
import Reveal from "@/components/Reveal";
import { useApi } from "@/components/useApi";
import type { TopicsData } from "@/lib/types";

export default function TopicsPage() {
  const { data, error, loading } = useApi<TopicsData>("topics");
  return (
    <div className="space-y-6">
      <div className="mb-7">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-accent">
          Taxonomy / coverage
        </div>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-text1 sm:text-3xl">
          Topic watchlist
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mute">
          Every doc is tagged with up to three topics by the zero-token keyword
          layer - the backbone of the trend views.
        </p>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="card p-5">
              <div className="skeleton h-4 w-40 rounded" />
              <div className="skeleton mt-3 h-3 w-full rounded" />
              <div className="skeleton mt-2 h-3 w-2/3 rounded" />
            </div>
          ))}
        </div>
      ) : error || !data ? (
        <div className="card max-w-xl border-neg/30 p-6 text-sm text-neg">
          {error || "No data"}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {data.topics.map((t, i) => (
            <Reveal key={t.key} delay={Math.min(60 * i, 300)}>
              <div className="card card-hoverable h-full p-5">
                <div className="flex items-baseline justify-between gap-3">
                  <h3 className="text-[15px] font-semibold text-text1">
                    {t.labelEn}
                  </h3>
                  <span className="shrink-0 font-mono text-[11px] tabular-nums text-mute">
                    {t.docs} docs
                  </span>
                </div>
                <div className="mt-1.5 flex items-center gap-2 font-mono text-[11px] text-mute">
                  <span className="uppercase tracking-wide">avg sentiment</span>
                  <span
                    className={
                      "font-semibold tabular-nums " +
                      (t.avgSentiment == null
                        ? "text-mute"
                        : t.avgSentiment >= 0.15
                          ? "text-pos"
                          : t.avgSentiment <= -0.15
                            ? "text-neg"
                            : "text-accent")
                    }
                  >
                    {t.avgSentiment == null ? "n/a" : t.avgSentiment.toFixed(2)}
                  </span>
                </div>
                <div className="mt-4">
                  <MixBar mix={t.mix} />
                </div>
                {t.latest && (
                  <div className="mt-3 border-t border-line pt-2.5 font-mono text-[10.5px] text-mute">
                    last doc {t.latest.slice(0, 10)}
                  </div>
                )}
              </div>
            </Reveal>
          ))}
        </div>
      )}
    </div>
  );
}
