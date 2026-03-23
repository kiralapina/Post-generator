import axios from "axios";

/** Пустая строка = относительные URL (production за nginx на одном origin). */
const baseURL = (() => {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (raw !== undefined && String(raw).trim() !== "") {
    return String(raw).replace(/\/$/, "");
  }
  if (import.meta.env.DEV) {
    // Тот же origin, что и Vite — запросы идут на dev-сервер и проксируются (см. vite.config.ts).
    return "";
  }
  return "";
})();

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
  timeout: 600_000,
});

export interface AnalyzeSiteResponse {
  url: string;
  steps: string[];
  intermediate_results: string[];
  final: Record<string, unknown>;
  final_analysis?: Record<string, unknown>;
}

export async function analyzeSite(url: string): Promise<AnalyzeSiteResponse> {
  const { data } = await api.post<AnalyzeSiteResponse>("/analyze-site", {
    url,
  });
  return data;
}
