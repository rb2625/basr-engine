"use client";

import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DayPoint } from "@/lib/types";

const GRID = "rgba(255,255,255,0.03)";

interface TooltipRow {
  dataKey?: string | number;
  name?: string | number;
  value?: number | string;
  color?: string;
  fill?: string;
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipRow[];
  label?: string | number;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-white/8 bg-[#141416]/95 px-3 py-2 font-mono text-[10px] shadow-lg backdrop-blur-md">
      <div className="mb-1 text-ink-3">{label}</div>
      {payload.map((p) => (
        <div key={String(p.dataKey)} className="flex items-center justify-between gap-4 tabular-nums">
          <span className="flex items-center gap-1.5 text-ink-3">
            <span
              className="inline-block h-1.5 w-1.5 rounded-full"
              style={{ backgroundColor: p.color || p.fill }}
            />
            {p.name}
          </span>
          <span className="text-ink-2">
            {typeof p.value === "number" ? p.value.toFixed(2) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export function SentimentSeries({ series }: { series: DayPoint[] }) {
  if (!series.length) {
    return (
      <div className="flex h-56 items-center justify-center font-mono text-[11px] text-ink-3">
        No time-series data yet
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart data={series} margin={{ top: 4, right: 4, bottom: 0, left: -16 }}>
        <defs>
          <linearGradient id="volFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#F59E0B" stopOpacity={0.01} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "#525252", fontSize: 9.5 }}
          interval="preserveStartEnd"
          minTickGap={40}
          axisLine={{ stroke: GRID }}
          tickLine={false}
        />
        <YAxis
          yAxisId="vol"
          tick={{ fill: "#525252", fontSize: 9.5 }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <YAxis
          yAxisId="sent"
          orientation="right"
          domain={[-1, 1]}
          tick={{ fill: "#525252", fontSize: 9.5 }}
          axisLine={false}
          tickLine={false}
          ticks={[-1, -0.5, 0, 0.5, 1]}
        />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ paddingTop: 6 }} />
        <Area
          yAxisId="vol"
          type="monotone"
          dataKey="volume"
          name="Docs"
          stroke="#F59E0B"
          strokeWidth={1.5}
          fill="url(#volFill)"
          animationDuration={900}
        />
        <Line
          yAxisId="sent"
          type="monotone"
          dataKey="avgSentiment"
          name="Avg sentiment"
          stroke="#4ADE80"
          strokeWidth={1.5}
          dot={false}
          animationDuration={900}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

const TOPIC_COLORS = ["#F87171", "#A855F7", "#F59E0B", "#60A5FA", "#4ADE80"];

export function StressStack({ series, topics }: { series: DayPoint[]; topics: string[] }) {
  if (!series.length)
    return (
      <div className="flex h-56 items-center justify-center font-mono text-[11px] text-ink-3">
        No data yet
      </div>
    );
  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart data={series} margin={{ top: 4, right: 4, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "#525252", fontSize: 9.5 }}
          interval="preserveStartEnd"
          minTickGap={40}
          axisLine={{ stroke: GRID }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "#525252", fontSize: 9.5 }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ paddingTop: 6 }} />
        <Bar
          dataKey="stress"
          name="Stress (all)"
          fill="#F87171"
          fillOpacity={0.8}
          radius={[3, 3, 0, 0]}
          animationDuration={900}
        />
        {topics.map((t, i) => (
          <Bar
            key={t}
            dataKey={`stressByTopic.${t}`}
            name={t.replace(/-/g, " ")}
            stackId="topic"
            fill={TOPIC_COLORS[i % TOPIC_COLORS.length]}
            fillOpacity={0.7}
            radius={i === topics.length - 1 ? [3, 3, 0, 0] : 0}
            animationDuration={900}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
