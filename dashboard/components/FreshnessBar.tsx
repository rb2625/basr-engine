"use client";

import { useEffect, useState } from "react";

interface Props {
  lastUpdated: Date | null;
  onRefresh: () => void;
  refreshing?: boolean;
}

function timeSince(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export default function FreshnessBar({ lastUpdated, onRefresh, refreshing }: Props) {
  const [, setTick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(id);
  }, []);

  const isStale = lastUpdated
    ? Date.now() - lastUpdated.getTime() > 120000
    : true;

  return (
    <div className="flex items-center gap-3">
      <div className={`live-indicator ${isStale ? "stale" : ""}`}>
        <span className="dot" aria-hidden="true" />
        {lastUpdated ? (
          <span>Updated {timeSince(lastUpdated)}</span>
        ) : (
          <span>Loading...</span>
        )}
      </div>
      <button
        onClick={onRefresh}
        disabled={refreshing}
        className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/5 bg-white/[0.02] text-ink-3 transition-all hover:border-white/10 hover:bg-white/[0.04] hover:text-ink-2 disabled:opacity-50"
        aria-label="Refresh data"
        title="Refresh"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={refreshing ? "animate-spin" : ""}
        >
          <path d="M21 2v6h-6" />
          <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
          <path d="M3 22v-6h6" />
          <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
        </svg>
      </button>
    </div>
  );
}
