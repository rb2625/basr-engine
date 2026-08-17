import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";

export const metadata: Metadata = {
  title: "BASR - UAE Economic Sentiment Intelligence",
  description:
    "Live public sentiment intelligence for the UAE market: entity map, topic trends, and early-warning feed.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-50 text-zinc-900">
        <header className="border-b border-zinc-200 bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
            <a href="/" className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 text-sm font-black text-white">
                B
              </span>
              <span className="text-lg font-bold tracking-tight">
                BASR
                <span className="ml-2 hidden text-xs font-normal text-zinc-500 sm:inline">
                  UAE Economic Sentiment Intelligence
                </span>
              </span>
            </a>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
              Live
            </span>
          </div>
        </header>
        <Nav />
        <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
        <footer className="mx-auto max-w-6xl px-4 pb-10 pt-4 text-xs text-zinc-400">
          BASR 2.0 - measured, not vibes. Classifiers are scored on a 500-item
          eval set; scores are published in this dashboard. Data refreshes
          continuously from public sources.
        </footer>
      </body>
    </html>
  );
}
