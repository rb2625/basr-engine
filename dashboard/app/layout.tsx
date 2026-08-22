import type { Metadata, Viewport } from "next";
import { Outfit, IBM_Plex_Mono } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";
import FloatingNav from "@/components/FloatingNav";
import ClientProviders from "@/components/ClientProviders";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

const ibmPlex = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

const notoKufi = localFont({
  src: "./fonts/NotoKufiArabic-Regular.woff2",
  variable: "--font-arabic",
  display: "swap",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export const metadata: Metadata = {
  title: "BASR | UAE Sentiment Intelligence",
  description:
    "Real-time public sentiment intelligence for the UAE. Arabic, Arabizi, and English.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${outfit.variable} ${ibmPlex.variable} ${notoKufi.variable}`}
    >
      <body className="min-h-screen font-body antialiased">
        <ClientProviders>
          <FloatingNav />
          <main className="mx-auto max-w-[1400px] px-4 pt-20 pb-24 sm:px-6 lg:px-8">
            {children}
          </main>
          <footer className="mx-auto max-w-[1400px] px-4 pb-28 sm:px-6 lg:px-8">
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/5 pt-4 text-[10px] text-ink-3">
              <div className="flex items-center gap-2">
                <span className="font-medium text-ink-2">BASR</span>
                <span className="font-mono text-ink-3">(بصر)</span>
                <span className="hidden sm:inline text-ink-faint">|</span>
                <span className="hidden sm:inline">5 data sources</span>
                <span className="hidden sm:inline text-ink-faint">|</span>
                <span className="hidden sm:inline">Arabic + Arabizi + English</span>
              </div>
              <div className="flex items-center gap-3">
                <a
                  href="https://github.com/rb2625/basr-engine"
                  target="_blank"
                  rel="noreferrer"
                  className="text-ink-3 transition-colors hover:text-ink-2"
                >
                  GitHub
                </a>
                <span className="text-ink-faint">|</span>
                <span className="font-mono">Apache 2.0</span>
              </div>
            </div>
          </footer>
        </ClientProviders>
      </body>
    </html>
  );
}
