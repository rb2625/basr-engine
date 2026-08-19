import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Nav from "@/components/Nav";
import FeedbackForm from "@/components/FeedbackForm";
import ClientProviders from "@/components/ClientProviders";
import UserMenu from "@/components/UserMenu";

const display = Inter({
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
  title: "BASR - UAE Sentiment Intelligence",
  description:
    "Real-time public sentiment intelligence for the UAE. Arabic, Arabizi, and English. Free, open, measured.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${display.variable} ${mono.variable}`}>
      <body className="min-h-screen antialiased">
        <ClientProviders>
          <header className="sticky top-0 z-30 border-b border-line bg-white/90 backdrop-blur-xl">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-4 sm:px-6 py-3.5">
              <a href="/" className="flex items-center gap-3 group">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent-dim text-sm font-bold text-white shadow-glow transition-shadow group-hover:shadow-glow-lg">
                  B
                </div>
                <div className="flex flex-col">
                  <span className="text-[15px] font-semibold tracking-tight text-ink">
                    BASR
                  </span>
                  <span className="hidden font-mono text-[10px] uppercase tracking-[0.15em] text-mute sm:block">
                    UAE Sentiment
                  </span>
                </div>
              </a>
              <div className="flex items-center gap-3">
                <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-line bg-panel2 px-3 py-1.5 font-mono text-[11px] text-mute">
                  5 sources / 550+ docs
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-pos/20 bg-pos-light px-3 py-1.5 text-[11px] font-medium text-pos">
                  <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-pos" />
                  Live
                </span>
                <UserMenu />
              </div>
            </div>
          </header>
          <Nav />
          <main className="mx-auto max-w-6xl px-4 sm:px-6 py-6 sm:py-8">{children}</main>
          <footer className="mx-auto max-w-6xl px-4 sm:px-6 pb-12 pt-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5 text-[11px] text-mute">
              <span className="font-medium text-ink">BASR <span className="font-mono text-mute">(بصر)</span></span>
              <div className="flex items-center gap-4">
                <a href="/privacy" className="hover:text-accent transition-colors duration-200">Privacy</a>
                <span className="font-mono">
                  88.3% sentiment accuracy | data from public sources
                </span>
              </div>
            </div>
          </footer>
          <FeedbackForm />
        </ClientProviders>
      </body>
    </html>
  );
}
