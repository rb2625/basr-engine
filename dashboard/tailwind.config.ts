import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0F172A",
        panel: "#FFFFFF",
        panel2: "#F8FAFC",
        line: "#E2E8F0",
        accent: "#6366F1",
        "accent-light": "#EEF2FF",
        "accent-dim": "#4F46E5",
        pos: "#16A34A",
        "pos-light": "#F0FDF4",
        neg: "#DC2626",
        "neg-light": "#FEF2F2",
        neu: "#64748B",
        "neu-light": "#F1F5F9",
        vio: "#7C3AED",
        "vio-light": "#F5F3FF",
        mute: "#94A3B8",
        text1: "#0F172A",
        gold: "#D97706",
        "gold-light": "#FFFBEB",
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.06), 0 1px 2px -1px rgba(0, 0, 0, 0.06)",
        "card-hover": "0 4px 12px -2px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.04)",
        lift: "0 12px 32px -12px rgba(0, 0, 0, 0.12)",
      },
      animation: {
        "pulse-dot": "pulseDot 2s ease-in-out infinite",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 0 0 rgba(22, 163, 74, 0.4)" },
          "50%": { opacity: "0.7", boxShadow: "0 0 0 6px rgba(22, 163, 74, 0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
