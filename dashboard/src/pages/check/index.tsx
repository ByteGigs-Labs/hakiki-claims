import { useCallback, useRef, useState } from "react";
import { AuditCard } from "../../components/AuditCard";
import { CitationDrawer } from "../../components/CitationDrawer";
import { ClaimFormPanel } from "../../components/ClaimFormPanel";
import { FixList } from "../../components/FixList";
import { GlassCube } from "../../components/GlassCube";
import { Icon } from "../../components/Icon";
import { NarrationPanel } from "../../components/NarrationPanel";
import { TraceTimeline } from "../../components/TraceTimeline";
import { VerdictBanner } from "../../components/VerdictBanner";
import { useAsync } from "../../hooks/useAsync";
import { checkClaim, errorMessage, fetchReference } from "../../lib/api";
import {
  applyPatch,
  changedFields,
  emptyForm,
  mergePatches,
  sampleClaim,
  sameClaim,
  toPayload,
  type ClaimForm,
} from "../../lib/claimForm";
import type { CheckResult, Fix, Language } from "../../types";
import "./check.css";

const FLASH_MS = 1700;
const PLACEHOLDER_LABEL: Record<string, string> = {
  preauth_ref: "the pre-authorisation reference",
  referral_ref: "the referral reference",
};

export function CheckClaimPage() {
  const reference = useAsync(fetchReference, []);
  const [form, setForm] = useState<ClaimForm>(emptyForm);
  const [result, setResult] = useState<CheckResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState<Language>("en");
  const [cited, setCited] = useState<string | null>(null);
  const [identical, setIdentical] = useState(false);
  const [flashing, setFlashing] = useState<ReadonlySet<keyof ClaimForm>>(new Set());
  const [placeholders, setPlaceholders] = useState<ReadonlySet<keyof ClaimForm>>(new Set());
  const previous = useRef<{ form: ClaimForm; hash: string } | null>(null);

  const run = useCallback(async (claim: ClaimForm) => {
    setBusy(true);
    setError(null);
    try {
      const data = await checkClaim(toPayload(claim));
      const last = previous.current;
      setIdentical(Boolean(last && sameClaim(last.form, claim) && last.hash === data.trace_hash));
      previous.current = { form: claim, hash: data.trace_hash };
      setResult(data);
    } catch (failure) {
      setError(errorMessage(failure, "This claim could not be checked. Please try again."));
    } finally {
      setBusy(false);
    }
  }, []);

  const edit = (next: ClaimForm) => {
    setPlaceholders((current) => new Set([...current].filter((key) => next[key] === form[key])));
    setForm(next);
  };

  const apply = (fixes: Fix[]) => {
    const next = applyPatch(form, mergePatches(fixes.map((fix) => fix.patch)));
    const changed = changedFields(form, next);
    setFlashing(new Set(changed));
    window.setTimeout(() => setFlashing(new Set()), FLASH_MS);
    setPlaceholders(
      (current) =>
        new Set([
          ...current,
          ...fixes.filter((fix) => fix.requires_input).flatMap((fix) => Object.keys(fix.patch) as (keyof ClaimForm)[]).filter((key) => key === "preauth_ref" || key === "referral_ref"),
        ]),
    );
    setForm(next);
    void run(next);
  };

  return (
    <div className="page check">
      <header className="page__header reveal">
        <p className="eyebrow">Glass box pre-audit</p>
        <h1>Know before you submit.</h1>
        <p>Every verdict comes with the rules it used, the SHA source behind them and the smallest fix.</p>
      </header>

      <div className="check__grid">
        <div className="check__form reveal" style={{ "--i": 1 } as React.CSSProperties}>
          <ClaimFormPanel
            form={form}
            reference={reference.data}
            busy={busy}
            flashing={flashing}
            placeholders={placeholders}
            onChange={edit}
            onSubmit={() => run(form)}
            onSample={() => {
              setForm(sampleClaim());
              setPlaceholders(new Set());
            }}
          />
        </div>

        <div className="check__result" aria-live="polite">
          {error && (
            <p className="check__error surface" role="alert">
              {error}
            </p>
          )}
          {!result && !error && (
            <div className="check__empty reveal" style={{ "--i": 2 } as React.CSSProperties}>
              <GlassCube />
              <h2>Your verdict appears here</h2>
              <p>Fill in the claim, or load the sample, to see the trace, the sources and the fixes.</p>
            </div>
          )}
          {result && (
            <>
              <VerdictBanner result={result} />
              {placeholders.size > 0 && (
                <p className="check__placeholder surface" role="status">
                  <Icon name="alert" size={18} />
                  This result uses a placeholder for {[...placeholders].map((key) => PLACEHOLDER_LABEL[key as string] ?? key).join(" and ")}. Replace it with the real reference before you submit the claim.
                </p>
              )}
              <div key={result.trace_hash + result.prev_hash} className="check__sections">
                {result.fixes.length > 0 && (
                  <div className="reveal" style={{ "--i": 0 } as React.CSSProperties}>
                    <FixList
                      fixes={result.fixes}
                      language={language}
                      busy={busy}
                      onApply={(fix) => apply([fix])}
                      onApplyAll={apply}
                    />
                  </div>
                )}
                <section className="trace-section reveal" style={{ "--i": 1 } as React.CSSProperties}>
                  <header className="section-head">
                    <div>
                      <p className="eyebrow">The glass box</p>
                      <h3>How the verdict was reached</h3>
                    </div>
                    <span className="chip">{result.trace.length} checks</span>
                  </header>
                  <TraceTimeline steps={result.trace} onCite={setCited} />
                </section>
                <div className="reveal" style={{ "--i": 2 } as React.CSSProperties}>
                  <NarrationPanel traceHash={result.trace_hash} language={language} onLanguage={setLanguage} />
                </div>
                <div className="reveal" style={{ "--i": 3 } as React.CSSProperties}>
                  <AuditCard result={result} identical={identical} busy={busy} onRerun={() => run(form)} />
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <CitationDrawer rule={cited} onClose={() => setCited(null)} />
    </div>
  );
}
