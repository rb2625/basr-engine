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

export function SentimentSeries({ series }: { series: DayPoint[] }) {
  if (!series.length) {
    return <div className="text-sm text-zinc-400">No time-series data yet</div>;
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={series} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" minTickGap={28} />
        <YAxis yAxisId="vol" tick={{ fontSize: 11 }} />
        <YAxis yAxisId="sent" orientation="right" domain={[-1, 1]} tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area
          yAxisId="vol"
          type="monotone"
          dataKey="volume"
          name="Docs"
          stroke="#f59e0b"
          fill="#f59e0b"
          fillOpacity={0.18}
        />
        <Line
          yAxisId="sent"
          type="monotone"
          dataKey="avgSentiment"
          name="Avg sentiment"
          stroke="#0d9488"
          strokeWidth={2}
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

const TOPIC_COLORS = ["#ef4444", "#8b5cf6", "#f59e0b", "#0ea5e9", "#10b981"];

export function StressStack({ series, topics }: { series: DayPoint[]; topics: string[] }) {
  if (!series.length) return <div className="text-sm text-zinc-400">No data yet</div>;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={series} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" minTickGap={28} />
        <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="stress" name="Stress (all)" fill="#ef4444" radius={[3, 3, 0, 0]} />
        {topics.map((t, i) => (
          <Bar
            key={t}
            dataKey={`stressByTopic.${t}`}
            name={t.replace(/-/g, " ")}
            stackId="topic"
            fill={TOPIC_COLORS[i % TOPIC_COLORS.length]}
            radius={i === topics.length - 1 ? [3, 3, 0, 0] : 0}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
