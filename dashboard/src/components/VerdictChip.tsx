import { VERDICT_LABEL } from "../lib/format";
import type { Verdict } from "../types";
import { VerdictMark } from "./VerdictMark";

export function VerdictChip({ verdict }: { verdict: Verdict }) {
  return (
    <span className={`verdict-chip verdict-chip--${verdict.toLowerCase()}`}>
      <VerdictMark verdict={verdict} size={20} animate={false} />
      {VERDICT_LABEL[verdict]}
    </span>
  );
}
