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
      className="card card-hoverable p-5 sm:p-6"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center gap-2">
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-mute">
          {label}
        </div>
        {tooltip && (
          <div className="tooltip-wrapper">
            <span className="inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-line text-[10px] text-mute transition-colors hover:border-accent hover:text-accent">
              ?
            </span>
            <span className="tooltip-content">{tooltip}</span>
          </div>
        )}
      </div>
      <div className="mt-3 flex items-baseline gap-1 font-mono text-[28px] font-semibold tabular-nums tracking-tight text-ink sm:text-[32px]">
        <CountUp value={num} decimals={decimals} />
        {suffix && <span className="text-[14px] font-medium text-accent">{suffix}</span>}
      </div>
      <div className="mt-1.5 text-[13px] text-mute">{sub}</div>
    </div>
  );
}
