import openapi from "../../docs/openapi.json";
import type { CheckResult, ClaimInput, Fix, Overview, TraceStep } from "./types";

type Keys<T> = Record<keyof T, true>;

const claimInput: Keys<ClaimInput> = {
  claim_ref: true,
  patient_token: true,
  patient_id: true,
  facility_id: true,
  service_code: true,
  fund: true,
  date_of_service: true,
  amount_kes: true,
  preauth_ref: true,
  icd_code: true,
  member_status: true,
  emergency: true,
  referral_ref: true,
  discharge_date: true,
  lodging_date: true,
};

const checkResult: Keys<CheckResult> = {
  claim: true,
  verdict: true,
  truth_value: true,
  revenue_at_risk_kes: true,
  trace: true,
  fixes: true,
  rulebook_version: true,
  trace_hash: true,
  prev_hash: true,
};

const traceStep: Keys<TraceStep> = {
  step: true,
  rule: true,
  result: true,
  fact: true,
  reason: true,
  values: true,
  stv: true,
  citation: true,
  premises: true,
};

const fix: Keys<Fix> = {
  action: true,
  action_sw: true,
  flips_to: true,
  rule: true,
  patch: true,
  requires_input: true,
};

const overview: Keys<Overview> = {
  days: true,
  since: true,
  checks: true,
  claims: true,
  passing: true,
  at_risk: true,
  will_fail: true,
  revenue_at_risk_kes: true,
  revenue_protected_kes: true,
  claims_protected: true,
  top_failing_rules: true,
  daily: true,
};

const schemas = openapi.components.schemas as unknown as Record<string, { properties: Record<string, unknown> }>;
const names = (schema: Record<string, true>) => Object.keys(schema).sort();
const properties = (name: string) => Object.keys(schemas[name]!.properties).sort();

describe("types.ts matches the frozen API contract", () => {
  it.each([
    ["ClaimInput", claimInput],
    ["CheckResult", checkResult],
    ["TraceStep", traceStep],
    ["Fix", fix],
    ["Overview", overview],
  ] as const)("%s has the same fields as the OpenAPI schema", (name, keys) => {
    expect(names(keys)).toEqual(properties(name));
  });
});
