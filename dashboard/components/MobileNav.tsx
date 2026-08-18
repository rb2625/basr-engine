"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/map", label: "Map" },
  { href: "/trends", label: "Trends" },
  { href: "/topics", label: "Topics" },
  { href: "/alerts", label: "Alerts" },
  { href: "/briefs", label: "Briefs" },
  { href: "/reports", label: "Reports" },
  { href: "/feed", label: "Feed" },
];

export default function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="lg:hidden">
      <button
        onClick={() => setOpen(!open)}
        className="flex h-8 w-8 items-center justify-center rounded-lg text-ink transition-colors hover:bg-panel2"
        aria-label="Toggle menu"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          {open ? (
            <path d="M4 4L14 14M14 4L4 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          ) : (
            <path d="M3 5H15M3 9H15M3 13H15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          )}
        </svg>
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm" onClick={() => setOpen(false)} />
          <div className="fixed inset-x-0 top-[56px] z-50 border-b border-line bg-white/95 p-4 shadow-lift backdrop-blur-xl">
            <nav className="flex flex-col gap-1">
              {LINKS.map((l) => {
                const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
                return (
                  <Link
                    key={l.href}
                    href={l.href}
                    onClick={() => setOpen(false)}
                    className={
                      "rounded-xl px-4 py-2.5 text-[14px] font-medium transition-colors " +
                      (active
                        ? "bg-accent/10 text-accent"
                        : "text-mute hover:bg-panel2 hover:text-ink")
                    }
                  >
                    {l.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </>
      )}
    </div>
  );
}
