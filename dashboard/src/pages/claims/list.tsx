import { useTable } from "@refinedev/core";
import { useState } from "react";
import { Icon } from "../../components/Icon";
import { Pagination } from "../../components/Pagination";
import { TraceDrawer } from "../../components/TraceDrawer";
import { VerdictChip } from "../../components/VerdictChip";
import { formatDateTime, kes } from "../../lib/format";
import type { ClaimRow } from "../../types";
import "./claims.css";

const COLUMNS: { field: string; label: string; numeric?: boolean }[] = [
  { field: "checked_at", label: "Checked" },
  { field: "service_code", label: "Service" },
  { field: "fund", label: "Fund" },
  { field: "amount_kes", label: "Billed", numeric: true },
  { field: "verdict", label: "Verdict" },
];

export function ClaimList() {
  const { result, tableQuery, currentPage, setCurrentPage, pageSize, sorters, setSorters } = useTable<ClaimRow>({
    resource: "claims",
    pagination: { currentPage: 1, pageSize: 10 },
    sorters: { initial: [{ field: "checked_at", order: "desc" }] },
    syncWithLocation: false,
  });
  const [open, setOpen] = useState<string | null>(null);
  const sorter = sorters[0];
  const rows = result.data;
  const total = result.total ?? 0;

  const sortBy = (field: string) =>
    setSorters([{ field, order: sorter?.field === field && sorter.order === "asc" ? "desc" : "asc" }]);

  return (
    <div className="page history">
      <header className="page__header reveal">
        <p className="eyebrow">Every check, on the record</p>
        <h1>Claims history</h1>
        <p>Open any check to replay its full reasoning and the sources behind it.</p>
      </header>

      <section className="ledger reveal" style={{ "--i": 1 } as React.CSSProperties}>
        <div className="ledger__head">
          {COLUMNS.map((column) => (
            <button
              key={column.field}
              type="button"
              className={`ledger__sort${column.numeric ? " ledger__sort--end" : ""}`}
              aria-label={`Sort by ${column.label}${sorter?.field === column.field ? `, ${sorter.order === "asc" ? "ascending" : "descending"}` : ""}`}
              onClick={() => sortBy(column.field)}
            >
              {column.label}
              <span className="ledger__caret" data-order={sorter?.field === column.field ? sorter.order : ""} />
            </button>
          ))}
          <span />
        </div>

        {tableQuery.isLoading && (
          <ul className="ledger__rows">
            {Array.from({ length: 6 }, (_, index) => (
              <li key={index} className="skeleton ledger__skeleton" />
            ))}
          </ul>
        )}

        {!tableQuery.isLoading && rows.length === 0 && (
          <div className="empty">
            <Icon name="history" size={56} />
            <h2>No checks yet</h2>
            <p>Claims you check will be listed here with their full reasoning.</p>
          </div>
        )}

        <ul className="ledger__rows">
          {rows.map((row, index) => (
            <li key={row.id} style={{ "--i": index } as React.CSSProperties} className="ledger__item reveal">
              <button type="button" className="ledger__row surface" onClick={() => setOpen(row.trace_hash)}>
                <span className="ledger__when">
                  {formatDateTime(row.checked_at)}
                  <small className="mono">{row.claim_ref}</small>
                </span>
                <span className="mono">{row.service_code}</span>
                <span>{row.fund}</span>
                <span className="tabular ledger__money">{kes(row.amount_kes)}</span>
                <VerdictChip verdict={row.verdict} />
                <span className="ledger__open" aria-hidden="true">
                  <Icon name="arrow" size={18} />
                </span>
              </button>
            </li>
          ))}
        </ul>
        <Pagination page={currentPage} pageSize={pageSize} total={total} onPage={setCurrentPage} />
      </section>

      <TraceDrawer traceHash={open} onClose={() => setOpen(null)} />
    </div>
  );
}
