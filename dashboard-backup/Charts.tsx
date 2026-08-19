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

const GRID = "#F1F5F9";

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
    <div className="rounded-lg border border-line bg-white px-3 py-2 font-mono text-[11px] shadow-lift">
      <div className="mb-1 text-mute">{label}</div>
      {payload.map((p) => (
        <div key={String(p.dataKey)} className="flex items-center justify-between gap-4 tabular-nums">
          <span className="flex items-center gap-1.5 text-mute">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: p.color || p.fill }}
            />
            {p.name}
          </span>
          <span className="text-text1">
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
      <div className="flex h-64 items-center justify-center font-mono text-xs text-mute">
        No time-series data yet
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={264}>
      <ComposedChart data={series} margin={{ top: 8, right: 8, bottom: 0, left: -14 }}>
        <defs>
          <linearGradient id="volFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366F1" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#6366F1" stopOpacity={0.01} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "#94A3B8", fontSize: 10.5 }}
          interval="preserveStartEnd"
          minTickGap={32}
          axisLine={{ stroke: GRID }}
          tickLine={false}
        />
        <YAxis
          yAxisId="vol"
          tick={{ fill: "#94A3B8", fontSize: 10.5 }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <YAxis
          yAxisId="sent"
          orientation="right"
          domain={[-1, 1]}
          tick={{ fill: "#94A3B8", fontSize: 10.5 }}
          axisLine={false}
          tickLine={false}
          ticks={[-1, -0.5, 0, 0.5, 1]}
        />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ paddingTop: 8 }} />
        <Area
          yAxisId="vol"
          type="monotone"
          dataKey="volume"
          name="Docs"
          stroke="#6366F1"
          strokeWidth={1.8}
          fill="url(#volFill)"
          animationDuration={1100}
        />
        <Line
          yAxisId="sent"
          type="monotone"
          dataKey="avgSentiment"
          name="Avg sentiment"
          stroke="#16A34A"
          strokeWidth={2}
          dot={false}
          animationDuration={1100}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

const TOPIC_COLORS = ["#DC2626", "#7C3AED", "#D97706", "#0284C7", "#16A34A"];

export function StressStack({ series, topics }: { series: DayPoint[]; topics: string[] }) {
  if (!series.length)
    return (
      <div className="flex h-64 items-center justify-center font-mono text-xs text-mute">
        No data yet
      </div>
    );
  return (
    <ResponsiveContainer width="100%" height={264}>
      <ComposedChart data={series} margin={{ top: 8, right: 8, bottom: 0, left: -14 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "#94A3B8", fontSize: 10.5 }}
          interval="preserveStartEnd"
          minTickGap={32}
          axisLine={{ stroke: GRID }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "#94A3B8", fontSize: 10.5 }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ paddingTop: 8 }} />
        <Bar
          dataKey="stress"
          name="Stress (all)"
          fill="#DC2626"
          fillOpacity={0.8}
          radius={[3, 3, 0, 0]}
          animationDuration={1100}
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
            animationDuration={1100}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
