import { useState } from "react";
import { useAsync } from "../hooks/useAsync";
import { verifyChain } from "../lib/api";
import { shortHash } from "../lib/format";
import type { CheckResult } from "../types";
import { Icon } from "./Icon";

function HashRow({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };
  return (
    <div className="hash">
      <dt>{label}</dt>
      <dd>
        <span className="mono" title={value}>
          {shortHash(value)}
        </span>
        <button type="button" className="btn btn--ghost" onClick={copy} aria-label={`Copy ${label}`}>
          <Icon name={copied ? "check" : "copy"} size={16} />
        </button>
      </dd>
    </div>
  );
}

interface Props {
  result: CheckResult;
  identical: boolean;
  busy: boolean;
  onRerun: () => void;
}

export function AuditCard({ result, identical, busy, onRerun }: Props) {
  const { data, loading } = useAsync(verifyChain, [result.trace_hash, result.prev_hash]);
  return (
    <section className="audit surface">
      <header className="section-head">
        <div>
          <p className="eyebrow">Tamper-evident audit log</p>
          <h3>Reproducible and chained</h3>
        </div>
        <span className={`seal${data && !data.valid ? " seal--broken" : ""}`}>
          {loading && (
            <>
              <span className="spinner" /> Verifying
            </>
          )}
          {data?.valid && (
            <>
              <Icon name="shield" size={16} /> Chain verified · {data.entries}
            </>
          )}
          {data && !data.valid && (
            <>
              <Icon name="alert" size={16} /> Broken at entry {data.broken_at}
            </>
          )}
        </span>
      </header>
      <dl className="hashes">
        <HashRow label="Trace hash" value={result.trace_hash} />
        <HashRow label="Previous entry" value={result.prev_hash} />
      </dl>
      <button type="button" className="btn btn--soft btn--small" disabled={busy} onClick={onRerun}>
        <Icon name="retry" size={16} /> Run the same claim again
      </button>
      {identical && (
        <p className="audit__match">
          <Icon name="check" size={16} /> Same claim, same rulebook: identical trace hash as the previous run.
        </p>
      )}
    </section>
  );
}
