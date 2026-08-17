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
  delay = 0,
}: {
  label: string;
  value: string;
  sub: string;
  delay?: number;
}) {
  const { num, decimals, suffix } = parseValue(value);
  return (
    <div
      className="card card-hoverable p-4 sm:p-5"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-mute">
        {label}
      </div>
      <div className="mt-2 flex items-baseline gap-1 font-mono text-[28px] font-semibold tabular-nums tracking-tight text-text1 sm:text-[32px]">
        <CountUp value={num} decimals={decimals} />
        <span className="text-[15px] text-gold">{suffix}</span>
      </div>
      <div className="mt-1.5 text-xs text-mute">{sub}</div>
    </div>
  );
}
