import { motion } from "framer-motion";

function formatKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/^\w/, (c) => c.toUpperCase());
}

type Props = {
  data: Record<string, unknown>;
  startIndex?: number;
};

export function FinalAnalysisCards({ data, startIndex = 0 }: Props) {
  const entries = Object.entries(data).filter(
    ([, v]) => v !== null && v !== undefined,
  );

  return (
    <div className="space-y-5">
      {entries.map(([key, value], i) => (
        <motion.section
          key={key}
          layout
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.06 * (startIndex + i),
            type: "spring",
            stiffness: 380,
            damping: 28,
          }}
          className="overflow-hidden rounded-2xl border border-white/10 bg-white/5 shadow-lg shadow-black/20"
        >
          <div className="border-b border-white/10 bg-white/5 px-4 py-3 sm:px-5">
            <h3 className="font-display text-lg font-semibold text-white">
              {formatKey(key)}
            </h3>
          </div>
          <div className="p-4 sm:p-5">
            <ValueBlock keyName={key} value={value} />
          </div>
        </motion.section>
      ))}
    </div>
  );
}

function ValueBlock({ keyName, value }: { keyName: string; value: unknown }) {
  const keyLower = keyName.toLowerCase();

  if (Array.isArray(value)) {
    const isExamplesKey = keyLower.includes("examples");
    if (isExamplesKey && value.length > 0) {
      return (
        <ul className="space-y-3">
          {value.map((item, idx) => (
            <motion.li
              key={idx}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.04 * idx }}
              className="rounded-xl border border-white/10 bg-slate-900/60 p-4 text-sm leading-relaxed text-slate-200"
            >
              {typeof item === "object"
                ? JSON.stringify(item, null, 2)
                : String(item)}
            </motion.li>
          ))}
        </ul>
      );
    }
    return (
      <ol className="list-decimal space-y-3 pl-5 text-sm text-slate-200">
        {value.map((item, idx) => (
          <li key={idx} className="leading-relaxed">
            {typeof item === "object"
              ? JSON.stringify(item, null, 2)
              : String(item)}
          </li>
        ))}
      </ol>
    );
  }

  if (typeof value === "object" && value !== null) {
    return (
      <pre className="overflow-x-auto whitespace-pre-wrap break-words text-xs text-slate-300">
        {JSON.stringify(value, null, 2)}
      </pre>
    );
  }

  return (
    <p className="whitespace-pre-wrap break-words text-sm leading-relaxed text-slate-200">
      {String(value)}
    </p>
  );
}
