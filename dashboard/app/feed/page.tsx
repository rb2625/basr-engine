"use client";

import { useState, useMemo } from "react";
import Reveal from "@/components/Reveal";
import Section from "@/components/Section";
import FreshnessBar from "@/components/FreshnessBar";
import { SignalBadge, SentimentBadge } from "@/components/Badge";
import { useApi } from "@/components/useApi";
import type { FeedData, FeedItem } from "@/lib/types";

function timeAgo(ts: string | null): string {
  if (!ts) return "unknown";
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const SOURCE_OPTIONS = ["all", "reddit", "news", "youtube", "app_store", "bluesky"];
const SENTIMENT_OPTIONS = ["all", "positive", "negative", "neutral", "mixed"];

export default function FeedPage() {
  const { data, error, loading, lastUpdated, refresh } =
    useApi<FeedData>("feed", "&limit=50", 120000);

  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [sentimentFilter, setSentimentFilter] = useState("all");

  const filtered = useMemo(() => {
    if (!data?.items) return [];
    return data.items.filter((f) => {
      const matchesSearch =
        !search ||
        f.title?.toLowerCase().includes(search.toLowerCase()) ||
        f.sector?.toLowerCase().includes(search.toLowerCase()) ||
        f.topics.some((t) => t.toLowerCase().includes(search.toLowerCase()));
      const matchesSource =
        sourceFilter === "all" || f.source === sourceFilter;
      const matchesSentiment =
        sentimentFilter === "all" || f.sentiment_label === sentimentFilter;
      return matchesSearch && matchesSource && matchesSentiment;
    });
  }, [data, search, sourceFilter, sentimentFilter]);

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-accent">
            Stream / classified docs
          </div>
          <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-ink sm:text-3xl">
            Classified feed
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-3">
            Latest docs with their sentiment, signal, sector, and topic tags.
          </p>
        </div>
        <FreshnessBar lastUpdated={lastUpdated} onRefresh={refresh} />
      </div>

      {loading ? (
        <div className="space-y-3">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="card p-5">
              <div className="skeleton h-4 w-3/4 rounded" />
              <div className="skeleton mt-3 h-3 w-1/3 rounded" />
            </div>
          ))}
        </div>
      ) : error || !data ? (
        <div className="card max-w-xl border-rose/30 p-6 text-sm text-rose">
          {error || "No data"}
        </div>
      ) : (
        <>
          {/* Search and filters */}
          <Reveal>
            <div className="card p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="relative flex-1">
                  <svg
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-3"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.3-4.3" />
                  </svg>
                  <input
                    type="text"
                    placeholder="Search titles, sectors, topics..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="search-input"
                    aria-label="Search feed"
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  {SOURCE_OPTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => setSourceFilter(s)}
                      className={`filter-chip ${sourceFilter === s ? "active" : ""}`}
                    >
                      {s === "all" ? "All sources" : s.replace("_", " ")}
                    </button>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  {SENTIMENT_OPTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => setSentimentFilter(s)}
                      className={`filter-chip ${sentimentFilter === s ? "active" : ""}`}
                    >
                      {s === "all" ? "All sentiment" : s}
                    </button>
                  ))}
                </div>
              </div>
              <div className="mt-2 font-mono text-[10px] text-ink-3">
                Showing {filtered.length} of {data.totalClassified} classified
                docs
              </div>
            </div>
          </Reveal>

          <Reveal delay={60}>
            <Section
              kicker="Stream"
              title="Latest classified docs"
              right={
                <span className="font-mono text-[11px] tabular-nums text-ink-3">
                  {data.totalClassified} classified in corpus
                </span>
              }
            >
              {filtered.length === 0 ? (
                <div className="py-8 text-center font-mono text-xs text-ink-3">
                  {search || sourceFilter !== "all" || sentimentFilter !== "all"
                    ? "No docs match your filters"
                    : "No classified docs yet - the NLP pipeline is warming up."}
                </div>
              ) : (
                <ul className="divide-y divide-white/5">
                  {filtered.map((f) => (
                    <li key={f.id} className="py-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="font-medium text-ink">{f.title}</div>
                          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[11px] text-ink-3">
                            <span className="uppercase tracking-wide">
                              {f.source}
                            </span>
                            <span className="tabular-nums">
                              {timeAgo(f.published_at)}
                            </span>
                            {f.sector && (
                              <span className="text-accentdim">{f.sector}</span>
                            )}
                            {f.sarcasm && (
                              <span className="font-semibold text-vio">
                                sarcasm
                              </span>
                            )}
                          </div>
                          {(f.topics.length > 0 || f.locations.length > 0) && (
                            <div className="mt-2.5 flex flex-wrap gap-1.5">
                              {f.topics.map((t) => (
                                <span
                                  key={t}
                                  className="rounded-md border border-white/5 bg-white/[0.03] px-1.5 py-0.5 font-mono text-[10px] text-ink-3"
                                >
                                  {t}
                                </span>
                              ))}
                              {f.locations.map((l) => (
                                <span
                                  key={l}
                        
