export type Verdict = "PASS" | "AT_RISK" | "WILL_FAIL";
export type Fund = "PHC" | "SHIF" | "ECCIF";
export type MemberStatus = "active" | "inactive" | "unknown";
export type Language = "en" | "sw";

export interface ClaimInput {
  claim_ref?: string;
  patient_token?: string; // pseudonymised ID, never a name
  patient_id?: string; // raw identifier; the API tokenises it and never stores it
  facility_id: string;
  service_code: string;
  fund: Fund;
  date_of_service: string; // YYYY-MM-DD
  amount_kes: number;
  preauth_ref?: string;
  icd_code?: string;
  member_status?: MemberStatus;
  emergency?: boolean;
  referral_ref?: string;
  discharge_date?: string;
  lodging_date?: string;
}

export interface TraceStep {
  step: number;
  rule: string;
  result: "pass" | "fail" | "warn" | "skip";
  fact: string;
  reason: string;
  values: Record<string, string | number>;
  stv?: [number, number];
  citation: string;
}

export interface Fix {
  action: string;
  action_sw: string;
  flips_to: Verdict;
  rule: string;
  patch: Partial<ClaimInput>;
  requires_input: boolean;
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
  claim_ref: string;
  service_code: string;
  fund: Fund;
  amount_kes: number;
  verdict: Verdict;
  revenue_at_risk_kes: number;
  trace_hash: string;
  checked_at: string;
}

export interface ReferenceData {
  rulebook_version: string;
  facilities: { id: string; name: string; level: number; funds: Fund[] }[];
  services: {
    id: string;
    name: string;
    levels: Partial<Record<Fund, number>>;
    preauth_funds: Fund[];
    funds: Fund[];
  }[];
  rules: { id: string; name: string }[];
}

export interface Identity {
  id: string;
  name: string;
  facility: string;
  role: "clerk" | "finance_manager" | "admin";
}

export interface Citation {
  rule: string;
  name: string;
  condition: string;
  document: string;
  section: string;
  url: string;
  effective: string;
  verified: boolean;
  quote: string;
  note: string;
}

export interface Narration {
  language: Language;
  text: string;
  source: "llm" | "template";
  verdict: Verdict;
}

export interface AuditStatus {
  valid: boolean;
  entries: number;
  head_hash: string;
  broken_at: number | null;
}

export interface BatchSummary {
  claims: number;
  pass: number;
  at_risk: number;
  will_fail: number;
  rows_rejected: number;
  revenue_at_risk_kes: number;
  top_failing_rules: { rule: string; name: string; count: number }[];
}

export interface Batch {
  id: string;
  filename: string;
  status: "queued" | "processing" | "done" | "failed";
  total: number;
  processed: number;
  errors: { row: number; fields: string[] }[];
  summary: BatchSummary | null;
  created_at: string;
  finished_at: string | null;
}

export interface BatchRow {
  row_number: number | null;
  claim_ref: string;
  service_code: string;
  fund: Fund;
  amount_kes: number;
  verdict: Verdict;
  revenue_at_risk_kes: number;
  failing_rules: string[];
  trace_hash: string;
}

export interface Overview {
  days: number;
  since: string;
  checks: number;
  claims: number;
  passing: number;
  at_risk: number;
  will_fail: number;
  revenue_at_risk_kes: number;
  revenue_protected_kes: number;
  claims_protected: number;
  top_failing_rules: { rule: string; name: string; count: number }[];
  daily: { date: string; checks: number; flagged: number }[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    fields?: { field: string; message: string }[];
  };
}
