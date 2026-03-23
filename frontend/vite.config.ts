import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/** В Docker: http://backend:8000. Локально без Docker: http://127.0.0.1:8000 */
const apiProxyTarget =
  process.env.VITE_API_PROXY_TARGET ?? "http://127.0.0.1:8000";

const proxyToBackend = {
  target: apiProxyTarget,
  changeOrigin: true,
} as const;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/analyze-site": proxyToBackend,
      "/chat-with-system": proxyToBackend,
      "/chat-json": proxyToBackend,
      "/chat": proxyToBackend,
      "/docs": proxyToBackend,
      "/openapi.json": proxyToBackend,
      "/redoc": proxyToBackend,
    },
  },
});
