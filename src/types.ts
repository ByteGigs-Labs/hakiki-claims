export type Verdict = "PASS" | "AT_RISK" | "WILL_FAIL";
export type Fund = "PHC" | "SHIF" | "ECCIF";

export interface ClaimInput {
  patient_token: string; // pseudonymised ID, never a name
  facility_id: string;
  service_code: string;
  fund: Fund;
  date_of_service: string; // YYYY-MM-DD
  amount_kes: number;
  preauth_ref?: string;
  icd_code?: string;
}

export interface TraceStep {
  step: number;
  rule: string;
  result: "pass" | "fail" | "warn";
  fact: string;
  stv?: [number, number];
  citation?: string;
}

export interface Fix {
  action: string;
  flips_to: Verdict;
}

export interface CheckResult {
  claim: string;
  verdict: Verdict;
  truth_value: { strength: number; confidence: number };
  revenue_at_risk_kes: number;
  trace: TraceStep[];
  fixes: Fix[];
  rulebook_version: string;
  trace_hash: string;
  prev_hash: string;
}

export interface ClaimRow {
  id: string;
  service_code: string;
  fund: Fund;
  amount_kes: number;
  verdict: Verdict;
  checked_at: string;
}
