/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
    "./lib/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif"
        ],
        mono: [
          "JetBrains Mono",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace"
        ]
      },
      colors: {
        background: "#050816",
        card: "#0B1020",
        cardSoft: "#111827",
        borderSoft: "#1F2937",
        accent: "#7C3AED",
        accentSoft: "#A78BFA",
        success: "#22C55E",
        warning: "#F59E0B",
        danger: "#EF4444"
      },
      boxShadow: {
        glow: "0 0 40px rgba(124, 58, 237, 0.25)",
        cyanGlow: "0 0 42px rgba(6, 182, 212, 0.22)",
        emeraldGlow: "0 0 42px rgba(16, 185, 129, 0.2)"
      },
      animation: {
        "pulse-soft": "pulseSoft 2.6s ease-in-out infinite"
      },
      keyframes: {
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.62" }
        }
      }
    }
  },
  plugins: []
};
