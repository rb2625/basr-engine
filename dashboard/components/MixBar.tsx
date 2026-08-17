import type { SignalMix } from "@/lib/types";

const COLORS: Record<keyof SignalMix, string> = {
  stress: "#ef4444",
  closure: "#8b5cf6",
  opportunity: "#10b981",
  neutral: "#a1a1aa",
};

const LABELS: Record<keyof SignalMix, string> = {
  stress: "Stress",
  closure: "Closure",
  opportunity: "Opportunity",
  neutral: "Neutral",
};

export default function MixBar({ mix }: { mix: SignalMix }) {
  const total = mix.stress + mix.closure + mix.opportunity + mix.neutral;
  if (!total) return <div className="text-xs text-zinc-400">No classified docs yet</div>;
  return (
    <div>
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-zinc-100">
        {(Object.keys(COLORS) as (keyof SignalMix)[]).map((k) => {
          const pct = (100 * mix[k]) / total;
          if (pct <= 0) return null;
          return (
            <div key={k} style={{ width: `${pct}%`, backgroundColor: COLORS[k] }} />
          );
        })}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-600">
        {(Object.keys(COLORS) as (keyof SignalMix)[]).map((k) => (
          <span key={k} className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: COLORS[k] }}
            />
            {LABELS[k]} {mix[k]}
          </span>
        ))}
      </div>
    </div>
  );
}
