import type { Verdict } from "../types";

const KES = new Intl.NumberFormat("en-KE", { maximumFractionDigits: 0 });
const DATE = new Intl.DateTimeFormat("en-KE", { day: "numeric", month: "short", year: "numeric" });
const DATE_TIME = new Intl.DateTimeFormat("en-KE", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

export const kes = (value: number) => `KES ${KES.format(Math.round(value))}`;

export const formatDate = (iso: string) => DATE.format(new Date(iso));

export const formatDateTime = (iso: string) => DATE_TIME.format(new Date(iso));

export const shortHash = (hash: string) => {
  const digest = hash.replace("sha256:", "");
  return `${digest.slice(0, 8)}…${digest.slice(-6)}`;
};

export const VERDICT_LABEL: Record<Verdict, string> = {
  PASS: "Will pass",
  AT_RISK: "At risk",
  WILL_FAIL: "Will fail",
};

export const VERDICT_HEADLINE: Record<Verdict, string> = {
  PASS: "Ready to submit",
  AT_RISK: "Needs a second look",
  WILL_FAIL: "Fix before submitting",
};

export const percent = (value: number) => `${Math.round(value * 100)}%`;

export const ruleId = (rule: string) => rule.split("-")[0] ?? rule;

export const ruleName = (rule: string) =>
  rule
    .split("-")
    .slice(1)
    .join("-")
    .replace(/([a-z])([A-Z])/g, "$1 $2");
