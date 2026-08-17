"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/map", label: "Map" },
  { href: "/trends", label: "Trends" },
  { href: "/topics", label: "Topics" },
  { href: "/feed", label: "Feed" },
];

export default function Nav() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-10 border-b border-line bg-ink/70 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 py-2">
        {LINKS.map((l) => {
          const active =
            l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={
                "rounded-lg px-3.5 py-1.5 text-[13px] font-medium transition-all duration-200 " +
                (active
                  ? "bg-gold/15 text-gold shadow-[inset_0_0_0_1px_rgba(231,184,78,0.35)]"
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
