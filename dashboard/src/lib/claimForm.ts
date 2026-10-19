import type { ClaimInput, Fund, MemberStatus } from "../types";

export interface ClaimForm {
  claim_ref: string;
  patient_id: string;
  facility_id: string;
  service_code: string;
  fund: Fund;
  date_of_service: string;
  amount_kes: string;
  member_status: MemberStatus;
  preauth_ref: string;
  icd_code: string;
}

export type FormErrors = Partial<Record<keyof ClaimForm, string>>;

export const SHA_LAUNCH = "2024-10-01";
const IDENTIFIER = /^[A-Za-z0-9][A-Za-z0-9._-]{0,49}$/;
const PREAUTH = /^[A-Za-z0-9][A-Za-z0-9/_-]{2,39}$/;
const ICD = /^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$/;
const PATIENT = /^[A-Za-z0-9 ._/-]{3,40}$/;

export const todayIso = (now = new Date()) => {
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
};

export const emptyForm = (): ClaimForm => ({
  claim_ref: "",
  patient_id: "",
  facility_id: "",
  service_code: "",
  fund: "SHIF",
  date_of_service: todayIso(),
  amount_kes: "",
  member_status: "active",
  preauth_ref: "",
  icd_code: "",
});

export const SAMPLE_CLAIM: ClaimForm = {
  claim_ref: "clm-104",
  patient_id: "DEMO-PATIENT-77",
  facility_id: "fac-12",
  service_code: "svc-CS-01",
  fund: "SHIF",
  date_of_service: "2026-10-14",
  amount_kes: "45000",
  member_status: "active",
  preauth_ref: "",
  icd_code: "",
};

export function validate(form: ClaimForm, today = todayIso()): FormErrors {
  const errors: FormErrors = {};
  if (form.claim_ref && !IDENTIFIER.test(form.claim_ref)) {
    errors.claim_ref = "Use letters, numbers, dot, dash or underscore";
  }
  if (!PATIENT.test(form.patient_id.trim())) errors.patient_id = "Enter the patient's identifier";
  if (!form.facility_id) errors.facility_id = "Choose a facility";
  if (!form.service_code) errors.service_code = "Choose a service";
  if (!form.date_of_service) errors.date_of_service = "Enter the date of service";
  else if (form.date_of_service < SHA_LAUNCH || form.date_of_service > today) {
    errors.date_of_service = "Must be between 1 Oct 2024 and today";
  }
  const amount = Number(form.amount_kes);
  if (!form.amount_kes || !Number.isFinite(amount) || amount <= 0 || amount > 10_000_000) {
    errors.amount_kes = "Enter an amount up to KES 10,000,000";
  } else if (Math.round(amount * 100) !== amount * 100) {
    errors.amount_kes = "Use at most two decimal places";
  }
  if (form.preauth_ref && !PREAUTH.test(form.preauth_ref)) {
    errors.preauth_ref = "Letters, numbers, slash, dash or underscore (3–40)";
  }
  if (form.icd_code && !ICD.test(form.icd_code)) errors.icd_code = "Use an ICD-10 code such as O82";
  return errors;
}

export function toPayload(form: ClaimForm): ClaimInput {
  const optional = (value: string) => (value.trim() ? value.trim() : undefined);
  return {
    claim_ref: optional(form.claim_ref),
    patient_id: form.patient_id.trim(),
    facility_id: form.facility_id,
    service_code: form.service_code,
    fund: form.fund,
    date_of_service: form.date_of_service,
    amount_kes: Number(form.amount_kes),
    member_status: form.member_status,
    preauth_ref: optional(form.preauth_ref),
    icd_code: optional(form.icd_code),
  };
}

export function applyPatch(form: ClaimForm, patch: Partial<ClaimInput>): ClaimForm {
  const next = { ...form };
  for (const [key, value] of Object.entries(patch)) {
    if (key in next && value !== undefined) {
      (next as Record<string, string>)[key] = String(value);
    }
  }
  return next;
}

export function changedFields(before: ClaimForm, after: ClaimForm): (keyof ClaimForm)[] {
  return (Object.keys(after) as (keyof ClaimForm)[]).filter((key) => before[key] !== after[key]);
}

export function mergePatches(patches: Partial<ClaimInput>[]): Partial<ClaimInput> {
  return Object.assign({}, ...patches);
}

export const sameClaim = (a: ClaimForm, b: ClaimForm) =>
  (Object.keys(a) as (keyof ClaimForm)[]).every((key) => a[key] === b[key]);
