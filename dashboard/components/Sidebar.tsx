"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  {
    href: "/",
    label: "Overview",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="2" width="5.5" height="5.5" rx="1.5" />
        <rect x="10.5" y="2" width="5.5" height="5.5" rx="1.5" />
        <rect x="2" y="10.5" width="5.5" height="5.5" rx="1.5" />
        <rect x="10.5" y="10.5" width="5.5" height="5.5" rx="1.5" />
      </svg>
    ),
  },
  {
    href: "/map",
    label: "Map",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 1.5C5.69 1.5 3 4.19 3 7.5C3 12.25 9 16.5 9 16.5C9 16.5 15 12.25 15 7.5C15 4.19 12.31 1.5 9 1.5Z" />
        <circle cx="9" cy="7.5" r="2.25" />
      </svg>
    ),
  },
  {
    href: "/trends",
    label: "Trends",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="2,13 6,9 10,11 16,4" />
        <polyline points="12,4 16,4 16,8" />
      </svg>
    ),
  },
  {
    href: "/topics",
    label: "Topics",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 4.5H16M2 9H12M2 13.5H8" />
      </svg>
    ),
  },
  {
    href: "/alerts",
    label: "Alerts",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7.15 2.93C7.73 2.32 8.61 2 9.5 2C11.99 2 14 4.01 14 6.5V9L16 12H2L4 9V6.5C4 4.01 6.01 2 8.5 2H7.15Z" />
        <path d="M7 13C7 14.1 7.9 15 9 15C10.1 15 11 14.1 11 13" />
      </svg>
    ),
  },
  {
    href: "/briefs",
    label: "Briefs",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.5 1.5H4.5C3.67 1.5 3 2.17 3 3V15C3 15.83 3.67 16.5 4.5 16.5H13.5C14.33 16.5 15 15.83 15 15V6L10.5 1.5Z" />
        <polyline points="10.5,1.5 10.5,6 15,6" />
        <line x1="6" y1="9.5" x2="12" y2="9.5" />
        <line x1="6" y1="12" x2="10" y2="12" />
      </svg>
    ),
  },
  {
    href: "/reports",
    label: "Reports",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2.5" y="1.5" width="13" height="15" rx="2" />
        <line x1="6" y1="5.5" x2="12" y2="5.5" />
        <line x1="6" y1="8.5" x2="12" y2="8.5" />
        <line x1="6" y1="11.5" x2="9" y2="11.5" />
      </svg>
    ),
  },
  {
    href: "/feed",
    label: "Feed",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 3H4.5V15H3C2.17 15 1.5 14.33 1.5 13.5V4.5C1.5 3.67 2.17 3 3 3Z" />
        <path d="M6 7H15M6 10.5H15M6 14H12" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex w-sidebar flex-col border-r border-border bg-surface sticky top-0 h-screen">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-border-subtle">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-sm font-bold text-white">
          B
        </div>
        <div className="flex flex-col">
          <span className="text-label-lg text-ink">BASR</span>
          <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-ink-faint">
            UAE Intelligence
          </span>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {LINKS.map((l) => {
          const active =
            l.href === "/"
              ? pathname === "/"
              : pathname.startsWith(l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`sidebar-link ${active ? "active" : ""}`}
            >
              <span className="shrink-0">{l.icon}</span>
              {l.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-border-subtle">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-1.5 w-1.5 rounded-full bg-positive animate-pulse-dot" />
          <span className="font-mono text-[10px] text-ink-faint">
            623 docs / 5 sources
          </span>
        </div>
        <div className="mt-2 font-mono text-[10px] text-ink-faint">
          88.3% accuracy
        </div>
      </div>
    </aside>
  );
}
