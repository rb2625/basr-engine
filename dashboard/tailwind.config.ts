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
        // Warm surface palette (not cold gray)
        canvas: "#F7F5F2",
        surface: "#FFFFFF",
        "surface-alt": "#FAF8F5",
        "surface-raised": "#FFFDFB",
        border: "#E8E4DF",
        "border-subtle": "#F0ECE7",

        // Ink: warm blacks, not cold grays
        ink: "#1C1917",
        "ink-secondary": "#44403C",
        "ink-tertiary": "#78716C",
        "ink-faint": "#A8A29E",

        // Accent: warm amber / burnt sand (UAE desert identity)
        accent: "#D97706",
        "accent-hover": "#B45309",
        "accent-light": "#FEF3C7",
        "accent-muted": "#FDE68A",
        "accent-deep": "#92400E",

        // Semantic
        positive: "#166534",
        "positive-light": "#F0FDF4",
        "positive-muted": "#BBF7D0",
        negative: "#991B1B",
        "negative-light": "#FEF2F2",
        "negative-muted": "#FECACA",
        neutral: "#57534E",
        "neutral-light": "#F5F5F4",
        caution: "#92400E",
        "caution-light": "#FFFBEB",
        info: "#1E40AF",
        "info-light": "#EFF6FF",

        // Violet for closures/signals
        violet: "#6D28D9",
        "violet-light": "#F5F3FF",
      },

      fontFamily: {
        display: ['"Outfit"', "system-ui", "sans-serif"],
        body: ['"Outfit"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
        arabic: ['"Noto Kufi Arabic"', '"Outfit"', "sans-serif"],
      },

      fontSize: {
        // Tighter, more intentional type scale
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
        xs: "0 1px 2px 0 rgba(28, 25, 23, 0.03)",
        DEFAULT: "0 1px 3px 0 rgba(28, 25, 23, 0.04), 0 1px 2px -1px rgba(28, 25, 23, 0.04)",
        md: "0 4px 6px -1px rgba(28, 25, 23, 0.05), 0 2px 4px -2px rgba(28, 25, 23, 0.04)",
        lg: "0 10px 15px -3px rgba(28, 25, 23, 0.06), 0 4px 6px -4px rgba(28, 25, 23, 0.04)",
        "card-hover": "0 8px 24px -8px rgba(28, 25, 23, 0.08), 0 2px 8px -4px rgba(28, 25, 23, 0.04)",
      },

      borderRadius: {
        sm: "6px",
        DEFAULT: "8px",
        md: "10px",
        lg: "14px",
        xl: "18px",
      },

      spacing: {
        "4.5": "1.125rem",
        "13": "3.25rem",
        "15": "3.75rem",
        "18": "4.5rem",
        "sidebar": "240px",
        "sidebar-collapsed": "64px",
      },

      animation: {
        "fade-in": "fadeIn 0.3s ease-out forwards",
        "slide-up": "slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-right": "slideRight 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "bar-grow": "barGrow 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "shimmer": "shimmer 1.5s ease-in-out infinite",
        "pulse-dot": "pulseDot 2s ease-in-out infinite",
        "count-up": "countUp 0.3s ease-out forwards",
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
        slideRight: {
          from: { opacity: "0", transform: "translateX(-6px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        barGrow: {
          from: { transform: "scaleX(0)" },
          to: { transform: "scaleX(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 0 0 rgba(22, 101, 52, 0.4)" },
          "50%": { opacity: "0.7", boxShadow: "0 0 0 4px rgba(22, 101, 52, 0)" },
        },
        countUp: {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
