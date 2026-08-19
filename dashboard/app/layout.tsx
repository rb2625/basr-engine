import type { Metadata } from "next";
import { Outfit, IBM_Plex_Mono } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
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
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 overflow-auto">
              <div className="mx-auto max-w-[1200px] px-6 py-6 lg:px-8 lg:py-8">
                {children}
              </div>
            </main>
          </div>
        </ClientProviders>
      </body>
    </html>
  );
}
