import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import axios from "axios";
import { analyzeSite, type AnalyzeSiteResponse } from "./api";
import { FinalAnalysisCards } from "./components/FinalAnalysisCards";
import { GlobalLoader } from "./components/GlobalLoader";

function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const d = err.response?.data;
    if (d && typeof d === "object" && "detail" in d) {
      const detail = (d as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail))
        return detail.map((x) => JSON.stringify(x)).join("; ");
    }
    if (err.code === "ECONNABORTED")
      return "Превышено время ожидания. Попробуйте позже или упростите сайт.";
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Неизвестная ошибка";
}

function pickFinal(data: AnalyzeSiteResponse): Record<string, unknown> {
  const raw = data.final_analysis ?? data.final;
  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    return raw as Record<string, unknown>;
  }
  return {};
}

export default function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeSiteResponse | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    const trimmed = url.trim();
    if (!trimmed) {
      setError("Введите ссылку на сайт.");
      return;
    }
    setLoading(true);
    try {
      const data = await analyzeSite(trimmed);
      setResult(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const finalData = result ? pickFinal(result) : null;

  return (
    <div className="min-h-screen px-4 py-10 sm:py-14">
      <div className="mx-auto w-full max-w-content">
        <motion.header
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="mb-10 text-center sm:mb-12"
        >
          <h1 className="font-display text-3xl font-bold tracking-tight text-white sm:text-4xl md:text-5xl">
            Идеи постов
            <span className="block bg-gradient-to-r from-indigo-300 to-fuchsia-300 bg-clip-text text-transparent">
              по содержанию сайта
            </span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-sm text-slate-400 sm:text-base">
            Вставьте URL — мы загрузим страницу, проанализируем текст и соберём
            варианты постов для соцсетей.
          </p>
        </motion.header>

        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.4 }}
          className="mb-10 space-y-4"
        >
          <label className="block text-left text-sm font-medium text-slate-300">
            Ссылка на сайт
            <input
              type="url"
              name="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              autoComplete="url"
              className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-base text-white placeholder:text-slate-500 outline-none ring-indigo-500/0 transition focus:border-indigo-400/50 focus:ring-2 focus:ring-indigo-500/30"
              disabled={loading}
            />
          </label>
          <motion.button
            type="submit"
            disabled={loading}
            whileHover={{ scale: loading ? 1 : 1.02 }}
            whileTap={{ scale: loading ? 1 : 0.98 }}
            className="w-full rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3.5 font-semibold text-white shadow-lg shadow-indigo-900/40 transition disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto sm:min-w-[200px]"
          >
            Отправить
          </motion.button>
        </motion.form>

        <AnimatePresence>
          {error && (
            <motion.div
              role="alert"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-8 overflow-hidden rounded-xl border border-rose-500/40 bg-rose-950/50 px-4 py-3 text-sm text-rose-100"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {loading && <GlobalLoader key="loader" />}
        </AnimatePresence>

        <AnimatePresence mode="wait">
          {result && !loading && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-10"
            >
              <motion.section
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-white/10 bg-white/5 p-5 sm:p-6"
              >
                <h2 className="font-display text-lg font-semibold text-white">
                  Источник
                </h2>
                <p className="mt-2 break-all text-sm text-indigo-200">
                  {result.url}
                </p>
              </motion.section>

              {result.steps?.length > 0 && (
                <motion.section
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 }}
                  className="rounded-2xl border border-white/10 bg-white/5 p-5 sm:p-6"
                >
                  <h2 className="font-display text-lg font-semibold text-white">
                    Шаги анализа
                  </h2>
                  <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-slate-300">
                    {result.steps.map((s, i) => (
                      <motion.li
                        key={i}
                        initial={{ opacity: 0, x: -6 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.04 * i }}
                      >
                        {s}
                      </motion.li>
                    ))}
                  </ol>
                </motion.section>
              )}

              {result.intermediate_results?.length > 0 && (
                <motion.section
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.08 }}
                  className="rounded-2xl border border-white/10 bg-white/5 p-5 sm:p-6"
                >
                  <h2 className="font-display text-lg font-semibold text-white">
                    Промежуточные результаты
                  </h2>
                  <div className="mt-4 space-y-4">
                    {result.intermediate_results.map((block, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.05 * i }}
                        className="rounded-xl border border-white/5 bg-slate-900/50 p-4 text-sm leading-relaxed text-slate-300"
                      >
                        {block}
                      </motion.div>
                    ))}
                  </div>
                </motion.section>
              )}

              {finalData && Object.keys(finalData).length > 0 && (
                <motion.section
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <h2 className="mb-6 font-display text-xl font-bold text-white">
                    Итоговый анализ
                  </h2>
                  <FinalAnalysisCards data={finalData} />
                </motion.section>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
