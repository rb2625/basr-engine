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
        ink: "#1A1D23",
        panel: "#FFFFFF",
        panel2: "#F8FAFC",
        line: "#E5E8EC",
        accent: "#6366F1",
        "accent-light": "#EEF2FF",
        "accent-dim": "#4F46E5",
        "accent-hover": "#818CF8",
        pos: "#15803D",
        "pos-light": "#F0FDF4",
        neg: "#B91C1C",
        "neg-light": "#FEF2F2",
        neu: "#475569",
        "neu-light": "#F8FAFC",
        vio: "#6D28D9",
        "vio-light": "#F5F3FF",
        mute: "#9CA3AF",
        text1: "#1A1D23",
        gold: "#B45309",
        "gold-light": "#FFFBEB",
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        "display-xl": ["2.5rem", { lineHeight: "1.1", letterSpacing: "-0.025em", fontWeight: "700" }],
        "display-lg": ["2rem", { lineHeight: "1.15", letterSpacing: "-0.02em", fontWeight: "700" }],
        "display-md": ["1.5rem", { lineHeight: "1.2", letterSpacing: "-0.015em", fontWeight: "600" }],
        "display-sm": ["1.25rem", { lineHeight: "1.25", letterSpacing: "-0.01em", fontWeight: "600" }],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)",
        "card-hover": "0 4px 16px -4px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04)",
        lift: "0 12px 32px -12px rgba(0, 0, 0, 0.12)",
        glow: "0 0 0 1px rgba(99, 102, 241, 0.1), 0 4px 16px -4px rgba(99, 102, 241, 0.12)",
        "glow-lg": "0 0 0 1px rgba(99, 102, 241, 0.15), 0 8px 32px -8px rgba(99, 102, 241, 0.2)",
      },
      animation: {
        "pulse-dot": "pulseDot 2s ease-in-out infinite",
        "fade-up": "fadeUp 0.6s cubic-bezier(0.22, 1.2, 0.36, 1) forwards",
        "fade-in": "fadeIn 0.4s ease-out forwards",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 0 0 rgba(21, 128, 61, 0.4)" },
          "50%": { opacity: "0.7", boxShadow: "0 0 0 6px rgba(21, 128, 61, 0)" },
        },
        fadeUp: {
          from: { opacity: "0", transform: "translateY(16px) scale(0.98)" },
          to: { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
      borderRadius: {
        "2xl": "14px",
      },
      spacing: {
        "4.5": "1.125rem",
        "13": "3.25rem",
        "15": "3.75rem",
        "18": "4.5rem",
        "88": "22rem",
        "128": "32rem",
      },
    },
  },
  plugins: [],
};
export default config;
