import { useState } from "react";
import { ActivityChart } from "../../components/ActivityChart";
import { CauseBars } from "../../components/CauseBars";
import { Icon } from "../../components/Icon";
import { useAsync } from "../../hooks/useAsync";
import { useCountUp } from "../../hooks/useCountUp";
import { errorMessage, fetchOverview } from "../../lib/api";
import { kes, percent } from "../../lib/format";
import type { Overview } from "../../types";
import "./overview.css";

const RANGES = [7, 30, 90];

function Figure({ label, value, caption, delay }: { label: string; value: number; caption: string; delay: number }) {
  const shown = useCountUp(value, 1500);
  return (
    <article className="figure surface reveal" style={{ "--i": delay } as React.CSSProperties}>
      <p className="eyebrow">{label}</p>
      <p className="figure__value tabular">{kes(shown)}</p>
      <p className="figure__caption">{caption}</p>
    </article>
  );
}

function Report({ data }: { data: Overview }) {
  const flagged = data.at_risk + data.will_fail;
  const share = data.claims ? flagged / data.claims : 0;
  return (
    <>
      <div className="overview__figures">
        <Figure
          label="Revenue protected"
          value={data.revenue_protected_kes}
          caption={`${data.claims_protected} ${data.claims_protected === 1 ? "claim was" : "claims were"} fixed before submission`}
          delay={0}
        />
        <Figure
          label="Revenue still at risk"
          value={data.revenue_at_risk_kes}
          caption={`${flagged} of ${data.claims} claims are still flagged`}
          delay={1}
        />
        <article className="figure surface reveal" style={{ "--i": 2 } as React.CSSProperties}>
          <p className="eyebrow">Claims flagged</p>
          <p className="figure__value tabular">{percent(share)}</p>
          <div className="split" role="img" aria-label={`${data.passing} pass, ${data.at_risk} at risk, ${data.will_fail} will fail`}>
            <span className="split__part split__part--pass" style={{ width: `${data.claims ? (data.passing / data.claims) * 100 : 0}%` }} />
            <span className="split__part split__part--risk" style={{ width: `${data.claims ? (data.at_risk / data.claims) * 100 : 0}%` }} />
            <span className="split__part split__part--fail" style={{ width: `${data.claims ? (data.will_fail / data.claims) * 100 : 0}%` }} />
          </div>
        </article>
      </div>

      <div className="overview__panels">
        <section className="surface overview__panel reveal" style={{ "--i": 3 } as React.CSSProperties}>
          <header className="section-head">
            <div>
              <p className="eyebrow">Activity</p>
              <h3>Claims checked each day</h3>
            </div>
            <span className="chip tabular">{data.checks} checks</span>
          </header>
          <ActivityChart daily={data.daily} />
        </section>
        <section className="surface overview__panel reveal" style={{ "--i": 4 } as React.CSSProperties}>
          {data.top_failing_rules.length > 0 ? (
            <CauseBars rules={data.top_failing_rules} title="Why claims are still flagged" />
          ) : (
            <div className="empty">
              <Icon name="shield" size={56} />
              <p>Nothing is flagged in this period.</p>
            </div>
          )}
        </section>
      </div>
    </>
  );
}

export function OverviewPage() {
  const [days, setDays] = useState(30);
  const { data, loading, error } = useAsync(() => fetchOverview(days), [days]);

  return (
    <div className="page overview">
      <header className="page__header reveal">
        <p className="eyebrow">Revenue, protected</p>
        <h1>Overview</h1>
        <p>What Hakiki caught before SHA did, and what is still waiting to be fixed.</p>
      </header>

      <div className="segmented overview__range reveal" style={{ "--count": RANGES.length, "--active": RANGES.indexOf(days) } as React.CSSProperties}>
        {RANGES.map((range) => (
          <button key={range} type="button" aria-pressed={range === days} onClick={() => setDays(range)}>
            {range} days
          </button>
        ))}
      </div>

      {loading && !data && <div className="skeleton" style={{ height: 320 }} />}
      {Boolean(error) && !loading && (
        <p className="check__error surface" role="alert">
          {errorMessage(error, "The overview is only available to finance managers and admins.")}
        </p>
      )}
      {data && data.claims === 0 && !loading && (
        <div className="empty surface">
          <Icon name="chart" size={56} />
          <h2>No claims in this period</h2>
          <p>Check a claim or upload a batch and the numbers appear here.</p>
        </div>
      )}
      {data && data.claims > 0 && <Report key={`${days}-${data.checks}`} data={data} />}
    </div>
  );
}
