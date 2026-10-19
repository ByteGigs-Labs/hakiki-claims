import { useCallback, useEffect, useRef, useState } from "react";
import { BatchRows } from "../../components/BatchRows";
import { Dropzone } from "../../components/Dropzone";
import { Icon } from "../../components/Icon";
import { ProgressRing } from "../../components/ProgressRing";
import { RevenueCard } from "../../components/RevenueCard";
import { downloadTemplate, errorMessage, fetchBatch, fetchRecentBatches, uploadBatch } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import type { Batch } from "../../types";
import "./batch.css";

const POLL_MS = 800;

type Phase = { kind: "idle" } | { kind: "uploading"; fraction: number; name: string } | { kind: "working"; batch: Batch };

export function BatchPage() {
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const [batch, setBatch] = useState<Batch | null>(null);
  const [recent, setRecent] = useState<Batch[]>([]);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number>(0);

  const loadRecent = useCallback(() => fetchRecentBatches(5).then(setRecent, () => undefined), []);

  useEffect(() => {
    void fetchRecentBatches(5).then((batches) => {
      setRecent(batches);
      const latest = batches.find((item) => item.status === "done");
      if (latest) setBatch(latest);
    }, () => undefined);
    return () => window.clearTimeout(timer.current);
  }, []);

  const follow = useCallback(
    (id: string) => {
      const tick = async () => {
        try {
          const current = await fetchBatch(id);
          if (current.status === "done" || current.status === "failed") {
            setPhase({ kind: "idle" });
            if (current.status === "done") setBatch(current);
            else setError("The batch could not be processed. Please try again.");
            void loadRecent();
            return;
          }
          setPhase({ kind: "working", batch: current });
          timer.current = window.setTimeout(tick, POLL_MS);
        } catch (failure) {
          setPhase({ kind: "idle" });
          setError(errorMessage(failure, "Lost contact with the server."));
        }
      };
      void tick();
    },
    [loadRecent],
  );

  const send = async (file: File) => {
    setError(null);
    setPhase({ kind: "uploading", fraction: 0, name: file.name });
    try {
      const accepted = await uploadBatch(file, (fraction) => setPhase({ kind: "uploading", fraction, name: file.name }));
      follow(accepted.id);
    } catch (failure) {
      setPhase({ kind: "idle" });
      setError(errorMessage(failure, "The file could not be uploaded."));
    }
  };

  const busy = phase.kind !== "idle";

  return (
    <div className="page batch">
      <header className="page__header reveal">
        <p className="eyebrow">A week of claims in one pass</p>
        <h1>Batch check</h1>
        <p>Upload a CSV and see which claims would fail, why, and how much revenue is at stake.</p>
      </header>

      <section className="batch__intake reveal" style={{ "--i": 1 } as React.CSSProperties}>
        <div className="batch__step surface">
          <span className="batch__no">1</span>
          <h2>Start from the template</h2>
          <p>One row per claim. Patient identifiers are hashed on arrival and never stored.</p>
          <button type="button" className="btn btn--soft" onClick={() => void downloadTemplate()}>
            <Icon name="download" size={18} /> Download template
          </button>
        </div>
        <div className="batch__step batch__step--drop surface">
          <span className="batch__no">2</span>
          {phase.kind === "idle" && <Dropzone disabled={busy} onFile={send} />}
          {phase.kind === "uploading" && (
            <ProgressRing fraction={phase.fraction} label={`${Math.round(phase.fraction * 100)}%`} caption={`Uploading ${phase.name}`} />
          )}
          {phase.kind === "working" && (
            <ProgressRing
              fraction={phase.batch.total ? phase.batch.processed / phase.batch.total : 0}
              label={`${phase.batch.processed}/${phase.batch.total}`}
              caption="Reasoning over every claim"
            />
          )}
        </div>
      </section>

      {error && (
        <p className="check__error surface" role="alert">
          {error}
        </p>
      )}

      {batch?.summary && (
        <div key={batch.id} className="batch__results">
          <header className="batch__meta reveal">
            <span className="chip">
              <Icon name="file" size={14} /> {batch.filename}
            </span>
            <span className="batch__time">{batch.finished_at ? formatDateTime(batch.finished_at) : ""}</span>
          </header>
          <div className="reveal" style={{ "--i": 1 } as React.CSSProperties}>
            <RevenueCard summary={batch.summary} />
          </div>
          {batch.errors.length > 0 && (
            <p className="batch__skipped surface reveal" style={{ "--i": 2 } as React.CSSProperties}>
              <Icon name="alert" size={18} />
              Skipped rows: {batch.errors.slice(0, 8).map((item) => `#${item.row} (${item.fields.join(", ")})`).join(" · ")}
              {batch.errors.length > 8 && ` and ${batch.errors.length - 8} more`}
            </p>
          )}
          <div className="reveal" style={{ "--i": 3 } as React.CSSProperties}>
            <BatchRows batchId={batch.id} />
          </div>
        </div>
      )}

      {recent.filter((item) => item.status === "done" && item.id !== batch?.id).length > 0 && (
        <section className="recent reveal">
          <p className="eyebrow">Earlier batches</p>
          <ul>
            {recent
              .filter((item) => item.status === "done" && item.id !== batch?.id)
              .map((item) => (
                <li key={item.id}>
                  <button type="button" className="btn btn--soft btn--small" onClick={() => setBatch(item)}>
                    <Icon name="file" size={14} /> {item.filename} · {formatDateTime(item.created_at)}
                  </button>
                </li>
              ))}
          </ul>
        </section>
      )}
    </div>
  );
}
