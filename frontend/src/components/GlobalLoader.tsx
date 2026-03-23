import { motion } from "framer-motion";

export function GlobalLoader() {
  return (
    <motion.div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-sm px-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <motion.div
        className="h-14 w-14 rounded-full border-2 border-indigo-400/30 border-t-indigo-400"
        animate={{ rotate: 360 }}
        transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
        aria-hidden
      />
      <p className="mt-6 text-center font-medium text-slate-200">
        Анализируем сайт...
      </p>
      <p className="mt-2 max-w-md text-center text-sm text-slate-400">
        Это может занять несколько минут: загрузка страницы и несколько запросов к
        модели.
      </p>
    </motion.div>
  );
}
