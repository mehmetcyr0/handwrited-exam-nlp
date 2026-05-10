/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
      },
      colors: {
        ink: { 950: "#0c1222", 900: "#151d2e", 700: "#3d4f72" },
        paper: { 50: "#f8fafc", 100: "#f1f5f9" },
        accent: { DEFAULT: "#2563eb", dim: "#1d4ed8" },
      },
    },
  },
  plugins: [],
};
