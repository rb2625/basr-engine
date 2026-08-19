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
        accent: "#F59E0B",
        "accent-dim": "#D97706",
        "accent-glow": "rgba(245, 158, 11, 0.15)",
        positive: "#4ADE80",
        negative: "#F87171",
        neutral: "#94A3B8",
        violet: "#A855F7",
        surface: "rgba(255, 255, 255, 0.03)",
        "surface-hover": "rgba(255, 255, 255, 0.06)",
        ink: "#F5F5F4",
        "ink-2": "#A8A29E",
        "ink-3": "#78716C",
        "ink-faint": "#525252",
      },
      fontFamily: {
        display: ['"Outfit"', "system-ui", "sans-serif"],
        body: ['"Outfit"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
        arabic: ['"Noto Kufi Arabic"', '"Outfit"', "sans-serif"],
      },
      fontSize: {
        "display-2xl": ["2rem", { lineHeight: "1.1", letterSpacing: "-0.03em", fontWeight: "700" }],
        "display-xl": ["1.5rem", { lineHeight: "1.15", letterSpacing: "-0.025em", fontWeight: "700" }],
        "display-lg": ["1.25rem", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "600" }],
        "display-sm": ["1rem", { lineHeight: "1.25", letterSpacing: "-0.01em", fontWeight: "600" }],
        "label-lg": ["0.8125rem", { lineHeight: "1.4", letterSpacing: "0.01em", fontWeight: "600" }],
        "label-sm": ["0.6875rem", { lineHeight: "1.4", letterSpacing: "0.04em", fontWeight: "600" }],
        "data-xl": ["1.75rem", { lineHeight: "1", letterSpacing: "-0.02em", fontWeight: "700" }],
        "data-lg": ["1.25rem", { lineHeight: "1", letterSpacing: "-0.01em", fontWeight: "600" }],
        "body-lg": ["0.9375rem", { lineHeight: "1.5", fontWeight: "400" }],
        "body-sm": ["0.8125rem", { lineHeight: "1.5", fontWeight: "400" }],
        "caption": ["0.6875rem", { lineHeight: "1.4", fontWeight: "500" }],
      },
      boxShadow: {
        glow: "0 0 20px -4px rgba(245, 158, 11, 0.15)",
        "glow-lg": "0 0 40px -8px rgba(245, 158, 11, 0.2)",
        "card-glow": "0 0 20px -4px rgba(245, 158, 11, 0.08), 0 8px 32px -8px rgba(0, 0, 0, 0.4)",
      },
      borderRadius: {
        sm: "6px",
        DEFAULT: "8px",
        md: "10px",
        lg: "14px",
        xl: "18px",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out forwards",
        "slide-up": "slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "bar-grow": "barGrow 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "pulse-dot": "pulseDot 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        barGrow: {
          from: { transform: "scaleX(0)" },
          to: { transform: "scaleX(1)" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 0 0 rgba(74, 222, 128, 0.4)" },
          "50%": { opacity: "0.7", boxShadow: "0 0 0 4px rgba(74, 222, 128, 0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
