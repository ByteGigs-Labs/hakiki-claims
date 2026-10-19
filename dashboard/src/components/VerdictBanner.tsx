import { useEffect, useRef, useState } from "react";
import { useCountUp } from "../hooks/useCountUp";
import { VERDICT_HEADLINE, VERDICT_LABEL, kes, percent } from "../lib/format";
import type { CheckResult, Verdict } from "../types";
import { TruthGauge } from "./TruthGauge";
import { VerdictMark } from "./VerdictMark";

function FlipWord({ verdict }: { verdict: Verdict }) {
  const [leaving, setLeaving] = useState<Verdict | null>(null);
  const shown = useRef(verdict);

  useEffect(() => {
    if (shown.current === verdict) return;
    setLeaving(shown.current);
    shown.current = verdict;
    const timer = window.setTimeout(() => setLeaving(null), 700);
    return () => window.clearTimeout(timer);
  }, [verdict]);

  return (
    <span className="flip" aria-live="polite">
      {leaving && (
        <span className="flip__word flip__word--out" aria-hidden="true">
          {VERDICT_LABEL[leaving]}
        </span>
      )}
      <span key={verdict} className="flip__word flip__word--in">
        {VERDICT_LABEL[verdict]}
      </span>
    </span>
  );
}

export function VerdictBanner({ result }: { result: CheckResult }) {
  const revenue = useCountUp(result.revenue_at_risk_kes, 1300);
  const { strength, confidence } = result.truth_value;
  return (
    <section className={`banner banner--${result.verdict.toLowerCase()} surface`}>
      <div className="banner__mark">
        <VerdictMark key={result.verdict} verdict={result.verdict} size={104} />
      </div>
      <div className="banner__body">
        <p className="eyebrow">Claim {result.claim}</p>
        <h2 className="banner__verdict">
          <FlipWord verdict={result.verdict} />
        </h2>
        <p className="banner__headline">{VERDICT_HEADLINE[result.verdict]}</p>
        <dl className="banner__facts">
          <div>
            <dt>Revenue at risk</dt>
            <dd className="tabular">{kes(revenue)}</dd>
          </div>
          <div>
            <dt>Rulebook</dt>
            <dd className="mono">{result.rulebook_version}</dd>
          </div>
        </dl>
      </div>
      <TruthGauge
        strength={strength}
        confidence={confidence}
        label={result.verdict === "PASS" ? "assurance" : "risk"}
      />
      <p className="banner__stv mono">
        stv ({strength.toFixed(2)}, {confidence.toFixed(2)}) · strength {percent(strength)} · confidence{" "}
        {percent(confidence)}
      </p>
    </section>
  );
}
