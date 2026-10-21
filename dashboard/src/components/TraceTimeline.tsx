import { useState } from "react";
import { useAsync } from "../hooks/useAsync";
import { fetchCitation, fetchReference } from "../lib/api";
import { percent, ruleId, ruleName } from "../lib/format";
import type { TraceStep } from "../types";
import { Icon } from "./Icon";

interface Props {
  steps: TraceStep[];
  onCite: (rule: string) => void;
}

const RESULT_LABEL: Record<TraceStep["result"], string> = {
  pass: "Passed",
  fail: "Failed",
  warn: "Needs review",
  skip: "Not evaluated",
};

function Node({ result }: { result: TraceStep["result"] }) {
  return (
    <span className={`trace__node trace__node--${result}`} aria-hidden="true">
      {result === "pass" && <Icon name="check" size={14} />}
      {result === "fail" && <Icon name="cross" size={14} />}
      {result === "warn" && <Icon name="alert" size={14} />}
    </span>
  );
}

function Logic({ step }: { step: TraceStep }) {
  const rule = ruleId(step.rule);
  const { data } = useAsync(() => fetchCitation(rule), [rule]);
  return (
    <div className="trace__logic">
      <p className="eyebrow">Facts the rule matched</p>
      <pre className="trace__atoms" tabIndex={0} aria-label="Matched facts">{(step.premises ?? []).join("\n") || "Recorded before premises were kept."}</pre>
      <p className="eyebrow">The rule itself, in MeTTa</p>
      {data ? <pre className="trace__atoms" tabIndex={0} aria-label="Rule source in MeTTa">{data.metta_source}</pre> : <div className="skeleton" style={{ height: 96 }} />}
    </div>
  );
}

function Step({ step, index, names, onCite }: { step: TraceStep; index: number; names: Map<string, string>; onCite: (rule: string) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <li className={`trace__step trace__step--${step.result}`} style={{ "--i": index } as React.CSSProperties}>
      <Node result={step.result} />
      <div className="trace__content">
        <div className="trace__head">
          <span className="trace__rule">
            <b>{ruleId(step.rule)}</b>
            {names.get(ruleId(step.rule)) ?? ruleName(step.rule)}
          </span>
          <span className="trace__result">
            {step.values.basis === "illustrative" && <span className="trace__basis">Placeholder cap</span>}
            {RESULT_LABEL[step.result]}
          </span>
        </div>
        <p className="trace__fact">{step.fact}</p>
        <div className="trace__foot">
          {step.stv && (
            <span className="trace__stv" title={`strength ${step.stv[0]}, confidence ${step.stv[1]}`}>
              <span className="trace__meter" style={{ "--v": step.stv[0] } as React.CSSProperties} />
              <span className="trace__meter trace__meter--thin" style={{ "--v": step.stv[1] } as React.CSSProperties} />
              <span className="mono">
                {percent(step.stv[0])} · {percent(step.stv[1])}
              </span>
            </span>
          )}
          <span className="trace__actions">
            <button type="button" className="chip" aria-expanded={open} onClick={() => setOpen(!open)}>
              <Icon name="code" size={14} /> {open ? "Hide the logic" : "Show the logic"}
            </button>
            <button type="button" className="chip" onClick={() => onCite(ruleId(step.rule))}>
              <Icon name="book" size={14} /> Source {ruleId(step.rule)}
            </button>
          </span>
        </div>
        {open && <Logic step={step} />}
      </div>
    </li>
  );
}

export function TraceTimeline({ steps, onCite }: Props) {
  const { data: reference } = useAsync(fetchReference, []);
  const names = new Map(reference?.rules.map((rule) => [rule.id, rule.name]));
  return (
    <ol className="trace">
      {steps.map((step, index) => (
        <Step key={step.step} step={step} index={index} names={names} onCite={onCite} />
      ))}
    </ol>
  );
}
