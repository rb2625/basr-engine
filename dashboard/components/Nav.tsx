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
    <nav className="sticky top-[52px] z-20 border-b border-line bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl gap-0.5 overflow-x-auto px-4 sm:px-6 py-1.5">
        {LINKS.map((l) => {
          const active =
            l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={
                "rounded-md px-3 py-1.5 text-[13px] font-medium whitespace-nowrap transition-colors duration-150 " +
                (active
                  ? "bg-accent/10 text-accent"
                  : "text-mute hover:bg-panel2 hover:text-text1")
              }
            >
              {l.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
