import { VERDICT_LABEL } from "../lib/format";
import type { Fix, Language } from "../types";
import { Icon } from "./Icon";
import { VerdictMark } from "./VerdictMark";

interface Props {
  fixes: Fix[];
  language: Language;
  busy: boolean;
  onApply: (fix: Fix) => void;
  onApplyAll: (fixes: Fix[]) => void;
}

export function FixList({ fixes, language, busy, onApply, onApplyAll }: Props) {
  return (
    <section className="fixes">
      <header className="section-head">
        <div>
          <p className="eyebrow">Counterfactual repairs</p>
          <h3>Smallest changes that fix it</h3>
        </div>
        {fixes.length > 1 && (
          <button type="button" className="btn btn--soft btn--small" disabled={busy} onClick={() => onApplyAll(fixes)}>
            <Icon name="spark" size={16} /> Apply all
          </button>
        )}
      </header>
      <ul className="fixes__list">
        {fixes.map((fix, index) => (
          <li key={fix.rule + fix.action} className="fix surface" style={{ "--i": index } as React.CSSProperties}>
            <VerdictMark verdict={fix.flips_to} size={44} animate={false} />
            <div className="fix__text">
              <p className="fix__action">{language === "sw" ? fix.action_sw : fix.action}</p>
              <p className="fix__meta">
                Resolves {fix.rule} · claim becomes <b>{VERDICT_LABEL[fix.flips_to].toLowerCase()}</b>
                {fix.requires_input && " · enter the real value afterwards"}
              </p>
            </div>
            <button type="button" className="btn btn--solid btn--small" disabled={busy} onClick={() => onApply(fix)}>
              Apply <Icon name="arrow" size={16} />
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
