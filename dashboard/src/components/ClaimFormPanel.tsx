import { useMemo, useState, type FormEvent } from "react";
import { validate, todayIso, SHA_LAUNCH, type ClaimForm, type FormErrors } from "../lib/claimForm";
import type { Fund, MemberStatus, ReferenceData } from "../types";
import { Icon } from "./Icon";

interface Props {
  form: ClaimForm;
  reference: ReferenceData | undefined;
  busy: boolean;
  flashing: ReadonlySet<keyof ClaimForm>;
  placeholders: ReadonlySet<keyof ClaimForm>;
  onChange: (next: ClaimForm) => void;
  onSubmit: () => void;
  onSample: () => void;
}

const FUNDS: Fund[] = ["PHC", "SHIF", "ECCIF"];
const MEMBER: { value: MemberStatus; label: string }[] = [
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "unknown", label: "Unconfirmed" },
];

interface FieldProps {
  name: keyof ClaimForm;
  label: string;
  error?: string;
  hint?: string;
  note?: string;
  children: React.ReactNode;
}

function Field({ label, error, hint, note, children }: FieldProps) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      {children}
      {error ? (
        <span className="field__hint" role="alert">
          {error}
        </span>
      ) : note ? (
        <span className="field__hint field__hint--note">{note}</span>
      ) : (
        hint && <span className="field__hint">{hint}</span>
      )}
    </label>
  );
}

export function ClaimFormPanel({ form, reference, busy, flashing, placeholders, onChange, onSubmit, onSample }: Props) {
  const [touched, setTouched] = useState(false);
  const errors: FormErrors = useMemo(() => (touched ? validate(form) : {}), [form, touched]);
  const set = <K extends keyof ClaimForm>(key: K, value: ClaimForm[K]) => onChange({ ...form, [key]: value });
  const input = (key: keyof ClaimForm) => ({
    className: `input${flashing.has(key) ? " flash" : ""}`,
    "aria-invalid": errors[key] ? true : undefined,
  });

  const service = reference?.services.find((item) => item.id === form.service_code);
  const facility = reference?.facilities.find((item) => item.id === form.facility_id);
  const level = service?.levels[form.fund];
  const serviceHint = !service
    ? undefined
    : level === undefined
      ? `Not offered under ${form.fund}`
      : `Level ${level}+${service.preauth_funds.includes(form.fund) ? " · needs pre-authorisation" : ""}`;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setTouched(true);
    if (Object.keys(validate(form)).length === 0) onSubmit();
  };

  return (
    <form className="claim-form surface" onSubmit={submit} noValidate>
      <header className="claim-form__head">
        <div>
          <p className="eyebrow">Before you submit</p>
          <h2>Check a claim</h2>
        </div>
        <button type="button" className="btn btn--ghost" onClick={onSample}>
          <Icon name="spark" size={16} /> Sample
        </button>
      </header>

      <Field name="patient_id" label="Patient identifier" error={errors.patient_id} hint="Hashed before checking. Never stored or logged.">
        <input {...input("patient_id")} value={form.patient_id} autoComplete="off" placeholder="SHA number or national ID" onChange={(e) => set("patient_id", e.target.value)} />
      </Field>

      <div className="claim-form__stack">
        <Field name="facility_id" label="Facility" error={errors.facility_id} hint={facility ? `KEPH level ${facility.level}` : undefined}>
          <select {...input("facility_id")} value={form.facility_id} onChange={(e) => set("facility_id", e.target.value)}>
            <option value="">Choose…</option>
            {reference?.facilities.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name} · L{item.level}
              </option>
            ))}
          </select>
        </Field>
        <Field name="service_code" label="Service" error={errors.service_code} hint={serviceHint}>
          <select {...input("service_code")} value={form.service_code} onChange={(e) => set("service_code", e.target.value)}>
            <option value="">Choose…</option>
            {reference?.services.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <div className="claim-form__pair">
        <Field name="fund" label="Fund" hint={service && !service.funds.includes(form.fund) ? "Not in this fund's package" : undefined}>
          <div className="segmented" style={{ "--count": 3, "--active": FUNDS.indexOf(form.fund) } as React.CSSProperties}>
            {FUNDS.map((fund) => (
              <button key={fund} type="button" aria-pressed={form.fund === fund} onClick={() => set("fund", fund)}>
                {fund}
              </button>
            ))}
          </div>
        </Field>
        <Field name="date_of_service" label="Date of service" error={errors.date_of_service}>
          <input {...input("date_of_service")} type="date" min={SHA_LAUNCH} max={todayIso()} value={form.date_of_service} onChange={(e) => set("date_of_service", e.target.value)} />
        </Field>
      </div>

      <Field name="amount_kes" label="Billed amount (KES)" error={errors.amount_kes}>
        <input {...input("amount_kes")} inputMode="decimal" value={form.amount_kes} placeholder="45000" onChange={(e) => set("amount_kes", e.target.value.replace(/[^0-9.]/g, ""))} />
      </Field>

      <Field name="member_status" label="Member's contribution status">
        <div className="segmented" style={{ "--count": 3, "--active": MEMBER.findIndex((m) => m.value === form.member_status) } as React.CSSProperties}>
          {MEMBER.map((item) => (
            <button key={item.value} type="button" aria-pressed={form.member_status === item.value} onClick={() => set("member_status", item.value)}>
              {item.label}
            </button>
          ))}
        </div>
      </Field>

      <div className="claim-form__pair">
        <Field name="emergency" label="Emergency service" hint="Waives pre-auth and referral">
          <div className="segmented" style={{ "--count": 2, "--active": form.emergency ? 1 : 0 } as React.CSSProperties}>
            <button type="button" aria-pressed={!form.emergency} onClick={() => set("emergency", false)}>
              No
            </button>
            <button type="button" aria-pressed={form.emergency} onClick={() => set("emergency", true)}>
              Yes
            </button>
          </div>
        </Field>
        <Field name="discharge_date" label="Discharge date" error={errors.discharge_date} hint="Inpatient only">
          <input {...input("discharge_date")} type="date" min={form.date_of_service} max={todayIso()} value={form.discharge_date} onChange={(e) => set("discharge_date", e.target.value)} />
        </Field>
      </div>

      <div className="claim-form__pair">
        <Field name="preauth_ref" label="Pre-authorisation ref." error={errors.preauth_ref} note={placeholders.has("preauth_ref") ? "Placeholder. Replace it with the real reference." : undefined}>
          <input {...input("preauth_ref")} value={form.preauth_ref} placeholder="If required" onChange={(e) => set("preauth_ref", e.target.value)} />
        </Field>
        <Field name="referral_ref" label="Referral ref." error={errors.referral_ref} note={placeholders.has("referral_ref") ? "Placeholder. Replace it with the real reference." : undefined} hint={form.fund === "SHIF" ? "SHIF is paid on referral" : undefined}>
          <input {...input("referral_ref")} value={form.referral_ref} placeholder="If required" onChange={(e) => set("referral_ref", e.target.value)} />
        </Field>
      </div>

      <div className="claim-form__pair">
        <Field name="icd_code" label="Diagnosis (ICD-10)" error={errors.icd_code} hint="Form 3 needs clinical details">
          <input {...input("icd_code")} value={form.icd_code} placeholder="O82" onChange={(e) => set("icd_code", e.target.value.toUpperCase())} />
        </Field>
        <Field name="claim_ref" label="Your claim reference" error={errors.claim_ref} hint="Catches duplicates">
          <input {...input("claim_ref")} value={form.claim_ref} placeholder="Optional" onChange={(e) => set("claim_ref", e.target.value)} />
        </Field>
      </div>

      <button type="submit" className="btn btn--solid btn--block" disabled={busy}>
        {busy ? <span className="spinner" /> : <Icon name="shield" size={18} />}
        {busy ? "Reasoning…" : "Check this claim"}
      </button>
    </form>
  );
}
