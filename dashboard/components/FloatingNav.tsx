"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4", color: "#818CF8" },
  { href: "/map", label: "Map", icon: "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7", color: "#34D399" },
  { href: "/trends", label: "Trends", icon: "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6", color: "#FBBF24" },
  { href: "/topics", label: "Topics", icon: "M4 6h16M4 12h16M4 18h7", color: "#C084FC" },
  { href: "/alerts", label: "Alerts", icon: "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9", color: "#FB7185" },
  { href: "/briefs", label: "Briefs", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z", color: "#22D3EE" },
  { href: "/reports", label: "Reports", icon: "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z", color: "#FBBF24" },
  { href: "/feed", label: "Feed", icon: "M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2.5 2.5 0 00-2.5-2.5H15", color: "#818CF8" },
];

export default function FloatingNav() {
  const pathname = usePathname();

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/[0.04]">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-3">
          <Link href="/" className="flex items-center gap-3 group" aria-label="BASR home">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo/10 text-indigo text-sm font-bold shadow-glow transition-all group-hover:shadow-glow-lg">
              B
            </div>
            <div className="flex flex-col">
              <span className="text-[14px] font-semibold text-ink tracking-tight">BASR</span>
              <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-ink-3">UAE Intelligence</span>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-white/5 bg-white/[0.02] px-3 py-1 font-mono text-[10px] text-ink-3">
              5 sources
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald/20 bg-emerald/5 px-2.5 py-1 text-[10px] font-medium text-emerald">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald animate-pulse-dot" aria-hidden="true" />
              Live
            </span>
          </div>
        </div>
      </header>

      <nav className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 nav-pill rounded-2xl px-2 py-1.5 flex items-center gap-0.5" aria-label="Main navigation">
        {LINKS.map((l) => {
          const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`nav-item ${active ? "active" : ""}`}
              title={l.label}
              aria-label={l.label}
              aria-current={active ? "page" : undefined}
              style={active ? { color: l.color } : undefined}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d={l.icon} />
              </svg>
              <span className="hidden sm:block">{l.label}</span>
              {active && (
                <span
                  className="absolute -bottom-1 left-1/2 -translate-x-1/2 h-0.5 w-4 rounded-full"
                  style={{ backgroundColor: l.color, boxShadow: `0 0 8px ${l.color}80` }}
                  aria-hidden="true"
                />
              )}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
