import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backend = "http://127.0.0.1:8000";

const proxy = {
  "/api": { target: backend, changeOrigin: true },
  "/health": { target: backend, changeOrigin: true },
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "127.0.0.1",
    strictPort: true,
    proxy,
  },
  preview: {
    port: 4173,
    host: "127.0.0.1",
    strictPort: true,
    proxy,
  },
});
