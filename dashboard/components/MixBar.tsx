import type { SignalMix } from "@/lib/types";

const COLORS: Record<keyof SignalMix, string> = {
  stress: "#F87171",
  closure: "#A855F7",
  opportunity: "#4ADE80",
  neutral: "#737373",
};

const LABELS: Record<keyof SignalMix, string> = {
  stress: "Stress",
  closure: "Closure",
  opportunity: "Opportunity",
  neutral: "Neutral",
};

const ORDER: (keyof SignalMix)[] = ["stress", "closure", "opportunity", "neutral"];

export default function MixBar({ mix }: { mix: SignalMix }) {
  const total = mix.stress + mix.closure + mix.opportunity + mix.neutral;
  if (!total)
    return <div className="font-mono text-[10px] text-ink-3">No classified docs yet</div>;

  let acc = 0;
  const segs = ORDER.map((k) => {
    const pct = (100 * mix[k]) / total;
    const seg = { k, pct, from: acc };
    acc += pct;
    return seg;
  }).filter((s) => s.pct > 0);

  return (
    <div>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-white/[0.04]">
        {segs.map((s, i) => (
          <div
            key={s.k}
            className="bar-grow"
            style={{
              width: `${s.pct}%`,
              backgroundColor: COLORS[s.k],
              animationDelay: `${i * 80}ms`,
            }}
          />
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 font-mono text-[9px] text-ink-3">
        {ORDER.map((k) => (
          <span key={k} className="inline-flex items-center gap-1.5 tabular-nums">
            <span
              className="inline-block h-1.5 w-1.5 rounded-full"
              style={{ backgroundColor: COLORS[k] }}
            />
            {LABELS[k]}
            <span className="text-ink-2">{mix[k]}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
