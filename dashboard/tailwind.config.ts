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
        // Primary accents
        indigo: "#818CF8",
        amber: "#FBBF24",
        emerald: "#34D399",
        rose: "#FB7185",
        violet: "#C084FC",
        cyan: "#22D3EE",
        // Semantic (aliases used across dashboard pages)
        positive: "#4ADE80",
        negative: "#F87171",
        neutral: "#94A3B8",
        accent: "#818CF8",
        "accent-dim": "#6366F1",
        accentdim: "#6366F1",
        neg: "#F87171",
        pos: "#4ADE80",
        neu: "#94A3B8",
        vio: "#C084FC",
        mute: "#737373",
        gold: "#FBBF24",
        // Surfaces
        ink: "#FAFAF9",
        "ink-2": "#A1A1AA",
        "ink-3": "#737373",
        "ink-faint": "#525252",
        surface: "#18181B",
        panel: "#1C1C20",
        "panel-2": "#222226",
        line: "rgba(255,255,255,0.06)",
        border: "rgba(255,255,255,0.06)",
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
        // Semantic aliases
        "text": ["0.9375rem", { lineHeight: "1.5", fontWeight: "400" }],
        body: ["0.9375rem", { lineHeight: "1.5", fontWeight: "400" }],
        display: ["1.25rem", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "600" }],
        label: ["0.8125rem", { lineHeight: "1.4", letterSpacing: "0.01em", fontWeight: "600" }],
        data: ["1.25rem", { lineHeight: "1", letterSpacing: "-0.01em", fontWeight: "600" }],
      },
      boxShadow: {
        glow: "0 0 20px -4px rgba(129, 140, 248, 0.2)",
        "glow-lg": "0 0 40px -8px rgba(129, 140, 248, 0.3)",
        "glow-amber": "0 0 20px -4px rgba(251, 191, 36, 0.2)",
        "glow-emerald": "0 0 20px -4px rgba(52, 211, 153, 0.2)",
        lift: "0 4px 24px -4px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)",
        large: "0 8px 40px -8px rgba(0,0,0,0.6)",
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
          "0%, 100%": { opacity: "1", boxShadow: "0 0 0 0 rgba(52, 211, 153, 0.4)" },
          "50%": { opacity: "0.7", boxShadow: "0 0 0 4px rgba(52, 211, 153, 0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
