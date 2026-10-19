import { useAsync } from "../hooks/useAsync";
import { explainCheck } from "../lib/api";
import type { Language } from "../types";
import { Icon } from "./Icon";

interface Props {
  traceHash: string;
  language: Language;
  onLanguage: (language: Language) => void;
}

const LANGUAGES: Language[] = ["en", "sw"];
const LABEL: Record<Language, string> = { en: "English", sw: "Kiswahili" };

export function NarrationPanel({ traceHash, language, onLanguage }: Props) {
  const { data, loading, error } = useAsync(() => explainCheck(traceHash, language), [traceHash, language]);
  const lines = data?.text.split("\n") ?? [];
  return (
    <section className="narration surface">
      <header className="section-head">
        <div>
          <p className="eyebrow">In plain language</p>
          <h3>{language === "sw" ? "Maelezo kwa mhudumu" : "Explained for the billing clerk"}</h3>
        </div>
        <div className="segmented" style={{ "--count": 2, "--active": LANGUAGES.indexOf(language) } as React.CSSProperties}>
          {LANGUAGES.map((code) => (
            <button key={code} type="button" aria-pressed={code === language} onClick={() => onLanguage(code)}>
              {LABEL[code]}
            </button>
          ))}
        </div>
      </header>
      {loading && <div className="skeleton" style={{ height: 110 }} />}
      {Boolean(error) && !loading && <p>The explanation is unavailable right now.</p>}
      {data && !loading && (
        <div className="narration__text" key={`${traceHash}-${language}`}>
          {lines.map((line, index) => (
            <p
              key={index}
              style={{ "--i": index } as React.CSSProperties}
              className={`reveal${line.startsWith("- ") ? " narration__point" : ""}`}
            >
              {line.replace(/^- /, "")}
            </p>
          ))}
        </div>
      )}
      {data && !loading && (
        <p className="narration__label">
          <Icon name="globe" size={14} />
          {data.source === "llm"
            ? "AI explanation. The verdict comes from the trace, never from the model."
            : "Generated from the trace. The verdict is decided by the rules, not by language."}
        </p>
      )}
    </section>
  );
}
