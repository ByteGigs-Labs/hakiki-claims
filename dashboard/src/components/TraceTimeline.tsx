import { useAsync } from "../hooks/useAsync";
import { fetchReference } from "../lib/api";
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

export function TraceTimeline({ steps, onCite }: Props) {
  const { data: reference } = useAsync(fetchReference, []);
  const names = new Map(reference?.rules.map((rule) => [rule.id, rule.name]));
  return (
    <ol className="trace">
      {steps.map((step, index) => (
        <li
          key={step.step}
          className={`trace__step trace__step--${step.result}`}
          style={{ "--i": index } as React.CSSProperties}
        >
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
              <button type="button" className="chip" onClick={() => onCite(ruleId(step.rule))}>
                <Icon name="book" size={14} /> Source {ruleId(step.rule)}
              </button>
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
