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
        // BASR signal-room palette (dark)
        ink: "#0A0E14",
        panel: "#10161F",
        panel2: "#151D29",
        line: "rgba(148, 163, 184, 0.14)",
        gold: "#E7B84E",
        golddim: "#B98A2E",
        pos: "#3DD68C",
        neg: "#F4656B",
        neu: "#5B6B7E",
        vio: "#A78BFA",
        mute: "#8B98A9",
        text1: "#E6EDF3",
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(231, 184, 78, 0.25), 0 8px 40px -12px rgba(231, 184, 78, 0.35)",
        lift: "0 12px 32px -12px rgba(0, 0, 0, 0.6)",
      },
      animation: {
        "pulse-dot": "pulseDot 2s ease-in-out infinite",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 0 0 rgba(61, 214, 140, 0.5)" },
          "50%": { opacity: "0.6", boxShadow: "0 0 0 6px rgba(61, 214, 140, 0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
