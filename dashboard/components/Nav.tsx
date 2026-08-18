"use client";

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

export default function Nav() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-[56px] z-20 border-b border-line bg-white/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 sm:px-6 py-2">
        {LINKS.map((l) => {
          const active =
            l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={
                "relative rounded-lg px-3.5 py-2 text-[13px] font-medium whitespace-nowrap transition-all duration-200 " +
                (active
                  ? "bg-accent/10 text-accent shadow-sm"
                  : "text-mute hover:bg-panel2 hover:text-ink")
              }
            >
              {l.label}
              {active && (
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 w-4 rounded-full bg-accent" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
