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
          <main className="mx-auto max-w-[1400px] px-6 pt-20 pb-24 lg:px-8">
            {children}
          </main>
          <footer className="mx-auto max-w-[1400px] px-6 pb-28 lg:px-8">
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/5 pt-4 text-[10px] text-ink-3">
              <span className="font-medium text-ink-2">BASR <span className="font-mono text-ink-3">(بصر)</span></span>
              <span className="font-mono">88.3% accuracy | public sources</span>
            </div>
          </footer>
        </ClientProviders>
      </body>
    </html>
  );
}
