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
    <nav className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4">
        {LINKS.map((l) => {
          const active =
            l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={
                "whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors " +
                (active
                  ? "border-amber-500 text-zinc-900"
                  : "border-transparent text-zinc-500 hover:border-zinc-300 hover:text-zinc-800")
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
