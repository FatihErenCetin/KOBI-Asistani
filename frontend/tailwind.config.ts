import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Plus Jakarta Sans", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
          950: "#022c22",
        },
        ink: {
          950: "#07111f",
        },
      },
      boxShadow: {
        soft: "0 18px 50px -28px rgba(15, 23, 42, 0.35)",
        card: "0 22px 70px -48px rgba(15, 23, 42, 0.55)",
        glow: "0 22px 60px -28px rgba(16, 185, 129, 0.45)",
      },
      backgroundImage: {
        "app-radial": "radial-gradient(circle at top left, rgba(16,185,129,.18), transparent 32rem), radial-gradient(circle at top right, rgba(59,130,246,.10), transparent 28rem)",
      },
    },
  },
  plugins: [],
};

export default config;
