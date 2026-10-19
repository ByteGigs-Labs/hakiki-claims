import { useEffect, useState } from "react";
import { useCountUp } from "../hooks/useCountUp";
import { kes } from "../lib/format";
import type { BatchSummary } from "../types";
import { CauseBars } from "./CauseBars";

export function RevenueCard({ summary }: { summary: BatchSummary }) {
  const [armed, setArmed] = useState(false);
  const revenue = useCountUp(summary.revenue_at_risk_kes, 1500);
  const flagged = summary.at_risk + summary.will_fail;
  const total = Math.max(summary.claims, 1);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setArmed(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  const share = (count: number) => `${armed ? (count / total) * 100 : 0}%`;

  return (
    <section className="revenue surface">
      <div className="revenue__headline">
        <p className="eyebrow">Revenue at risk in this batch</p>
        <p className="revenue__amount tabular">{kes(revenue)}</p>
        <p className="revenue__sub">
          <b className="tabular">{flagged}</b> of <b className="tabular">{summary.claims}</b> claims would be flagged
          {summary.rows_rejected > 0 && ` · ${summary.rows_rejected} rows could not be read`}
        </p>
      </div>

      <div className="split" role="img" aria-label={`${summary.pass} pass, ${summary.at_risk} at risk, ${summary.will_fail} will fail`}>
        <span className="split__part split__part--pass" style={{ width: share(summary.pass) }} />
        <span className="split__part split__part--risk" style={{ width: share(summary.at_risk) }} />
        <span className="split__part split__part--fail" style={{ width: share(summary.will_fail) }} />
      </div>
      <ul className="split__legend">
        <li><i className="split__key split__key--pass" /> Will pass <b className="tabular">{summary.pass}</b></li>
        <li><i className="split__key split__key--risk" /> At risk <b className="tabular">{summary.at_risk}</b></li>
        <li><i className="split__key split__key--fail" /> Will fail <b className="tabular">{summary.will_fail}</b></li>
      </ul>

      <CauseBars rules={summary.top_failing_rules} />
    </section>
  );
}
