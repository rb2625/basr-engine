import type { Metadata } from "next";
import { JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";
import Logo from "@/components/Logo";
import Clock from "@/components/Clock";
import Nav from "@/components/Nav";

const display = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "BASR بصيرة - UAE Economic Sentiment Intelligence",
  description:
    "Live public sentiment intelligence for the UAE market: entity map, topic trends, and early-warning feed. Measured, not vibes.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${display.variable} ${mono.variable}`}>
      <body className="bg-ambient min-h-screen antialiased">
        <header className="relative z-20 border-b border-line bg-ink/80 backdrop-blur-md">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3.5">
            <a href="/" className="group flex items-center gap-3">
              <Logo />
              <span className="flex flex-col leading-none">
                <span className="flex items-baseline gap-2">
                  <span className="text-lg font-bold tracking-[0.18em] text-text1">
                    BASR
                  </span>
                  <span className="font-mono text-[11px] tracking-widest text-gold">
                    بصيرة
                  </span>
                </span>
                <span className="mt-1 hidden text-[10.5px] uppercase tracking-[0.22em] text-mute sm:block">
                  UAE Economic Sentiment Intelligence
                </span>
              </span>
            </a>
            <div className="flex items-center gap-4">
              <Clock />
              <span className="inline-flex items-center gap-2 rounded-full border border-pos/30 bg-pos/10 px-3 py-1 text-[11px] font-medium tracking-wide text-pos">
                <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-pos" />
                LIVE
              </span>
            </div>
          </div>
        </header>
        <Nav />
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
        <footer className="mx-auto max-w-6xl px-4 pb-12 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5 font-mono text-[11px] text-mute">
            <span>BASR 2.0 / بصيرة - measured, not vibes</span>
            <span>
              classifiers scored on a 500-item eval set | data refreshes
              continuously from public sources
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
