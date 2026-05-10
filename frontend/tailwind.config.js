/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "system-ui", "sans-serif"],
      },
      colors: {
        ink: { 950: "#0f172a", 900: "#1e293b", 800: "#334155", 700: "#475569", 600: "#64748b" },
        paper: { 50: "#f8fafc", 100: "#f1f5f9", 200: "#e2e8f0" },
        accent: { DEFAULT: "#4f46e5", dim: "#4338ca", glow: "#6366f1" },
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.04), 0 12px 32px -8px rgba(15, 23, 42, 0.12)",
        "card-hover": "0 1px 2px rgba(15, 23, 42, 0.04), 0 20px 40px -12px rgba(15, 23, 42, 0.16)",
        glow: "0 0 0 1px rgba(99, 102, 241, 0.12), 0 8px 24px -4px rgba(79, 70, 229, 0.25)",
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
