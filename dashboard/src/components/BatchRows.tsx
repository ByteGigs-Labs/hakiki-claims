import { useState } from "react";
import { useAsync } from "../hooks/useAsync";
import { fetchBatchRows } from "../lib/api";
import { kes } from "../lib/format";
import type { Verdict } from "../types";
import { Icon } from "./Icon";
import { Pagination } from "./Pagination";
import { TraceDrawer } from "./TraceDrawer";
import { VerdictChip } from "./VerdictChip";

const PAGE_SIZE = 10;
const FILTERS: { value: Verdict | undefined; label: string }[] = [
  { value: undefined, label: "All" },
  { value: "WILL_FAIL", label: "Will fail" },
  { value: "AT_RISK", label: "At risk" },
  { value: "PASS", label: "Will pass" },
];

export function BatchRows({ batchId }: { batchId: string }) {
  const [filter, setFilter] = useState<Verdict | undefined>(undefined);
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState<string | null>(null);
  const { data, loading } = useAsync(
    () => fetchBatchRows(batchId, { verdict: filter, start: (page - 1) * PAGE_SIZE, end: page * PAGE_SIZE }),
    [batchId, filter, page],
  );
  const active = Math.max(FILTERS.findIndex((item) => item.value === filter), 0);

  return (
    <section className="batch-rows">
      <header className="section-head">
        <div>
          <p className="eyebrow">Claim by claim</p>
          <h3>Results</h3>
        </div>
        <div className="segmented" style={{ "--count": FILTERS.length, "--active": active } as React.CSSProperties}>
          {FILTERS.map((item) => (
            <button
              key={item.label}
              type="button"
              aria-pressed={item.value === filter}
              onClick={() => {
                setFilter(item.value);
                setPage(1);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </header>

      {loading && !data && <div className="skeleton" style={{ height: 280 }} />}
      {data && data.rows.length === 0 && (
        <div className="empty">
          <Icon name="filter" size={56} />
          <p>No claims match this filter.</p>
        </div>
      )}
      {data && (
        <ul className="rows" key={`${filter}-${page}`}>
          {data.rows.map((row, index) => (
            <li key={row.trace_hash + row.row_number} className="reveal" style={{ "--i": index } as React.CSSProperties}>
              <button type="button" className="rows__item surface" onClick={() => setOpen(row.trace_hash)}>
                <span className="rows__no tabular">#{row.row_number}</span>
                <span className="rows__ref">
                  <b className="mono">{row.claim_ref}</b>
                  <small className="mono">{row.service_code}</small>
                </span>
                <span className="tabular">{kes(row.amount_kes)}</span>
                <span className="rows__rules">
                  {row.failing_rules.map((rule) => (
                    <span key={rule} className="chip">
                      {rule}
                    </span>
                  ))}
                </span>
                <span className="tabular rows__risk">{row.revenue_at_risk_kes > 0 ? kes(row.revenue_at_risk_kes) : "—"}</span>
                <VerdictChip verdict={row.verdict} />
              </button>
            </li>
          ))}
        </ul>
      )}
      {data && <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPage={setPage} />}
      <TraceDrawer traceHash={open} onClose={() => setOpen(null)} />
    </section>
  );
}
