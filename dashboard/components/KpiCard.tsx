"use client";

import CountUp from "@/components/CountUp";

function parseValue(v: string): { num: number; decimals: number; suffix: string } {
  const m = v.match(/^(-?\d+(?:\.\d+)?)(.*)$/);
  if (!m) return { num: 0, decimals: 0, suffix: v };
  const raw = m[1];
  const decimals = raw.includes(".") ? raw.split(".")[1].length : 0;
  return { num: parseFloat(raw), decimals, suffix: m[2] };
}

export default function KpiCard({
  label,
  value,
  sub,
  tooltip,
  delay = 0,
}: {
  label: string;
  value: string;
  sub: string;
  tooltip?: string;
  delay?: number;
}) {
  const { num, decimals, suffix } = parseValue(value);
  return (
    <div
      className="card card-glow p-4"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center gap-1.5">
        <span className="font-label-sm uppercase tracking-widest text-ink-3">
          {label}
        </span>
        {tooltip && (
          <span className="tooltip-trigger">
            <span className="inline-flex h-3.5 w-3.5 cursor-help items-center justify-center rounded-full border border-white/10 text-[9px] text-ink-3 transition-colors hover:border-accent hover:text-accent">
              ?
            </span>
            <span className="tooltip-text">{tooltip}</span>
          </span>
        )}
      </div>
      <div className="mt-2.5 font-data-xl text-ink">
        <CountUp value={num} decimals={decimals} />
        {suffix && <span className="ml-0.5 text-data-lg text-accent font-medium">{suffix}</span>}
      </div>
      <div className="mt-1 font-caption text-ink-3">{sub}</div>
    </div>
  );
}
