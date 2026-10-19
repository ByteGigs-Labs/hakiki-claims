import {
  sampleClaim,
  applyPatch,
  changedFields,
  emptyForm,
  mergePatches,
  sameClaim,
  todayIso,
  toPayload,
  validate,
  type ClaimForm,
} from "./claimForm";

const TODAY = "2026-10-19";
const valid: ClaimForm = sampleClaim(TODAY);

describe("validate", () => {
  it("accepts the sample claim, dated two days before today", () => {
    expect(validate(valid, TODAY)).toEqual({});
    expect(valid.date_of_service).toBe("2026-10-17");
  });

  it("flags every required field of an empty form", () => {
    const errors = validate({ ...emptyForm(), date_of_service: "" }, TODAY);
    expect(Object.keys(errors).sort()).toEqual(
      ["amount_kes", "date_of_service", "facility_id", "patient_id", "service_code"].sort(),
    );
  });

  it.each([
    ["amount_kes", "0"],
    ["amount_kes", "-5"],
    ["amount_kes", "10000001"],
    ["amount_kes", "12.345"],
    ["date_of_service", "2024-09-30"],
    ["date_of_service", "2026-10-20"],
    ["preauth_ref", "no spaces"],
    ["icd_code", "o82"],
    ["claim_ref", "bad ref"],
    ["referral_ref", "no spaces"],
    ["discharge_date", "2026-10-10"],
    ["discharge_date", "2026-10-20"],
    ["patient_id", "ab"],
  ] as const)("rejects %s = %s", (field, value) => {
    expect(validate({ ...valid, [field]: value }, TODAY)[field]).toBeTruthy();
  });

  it("allows blank optional fields", () => {
    expect(validate({ ...valid, preauth_ref: "", icd_code: "", claim_ref: "" }, TODAY)).toEqual({});
  });
});

describe("toPayload", () => {
  it("sends the raw patient identifier and drops blank optionals", () => {
    const payload = toPayload({ ...valid, claim_ref: "", preauth_ref: "  ", icd_code: "", discharge_date: "" });
    expect(payload.discharge_date).toBeUndefined();
    expect(payload.emergency).toBe(false);
    expect(payload).toMatchObject({ patient_id: "DEMO-PATIENT-77", amount_kes: 45000, fund: "SHIF" });
    expect(payload.claim_ref).toBeUndefined();
    expect(payload.preauth_ref).toBeUndefined();
    expect(payload).not.toHaveProperty("patient_token");
  });
});

describe("fix patches", () => {
  it("applies a patch as strings and reports what changed", () => {
    const next = applyPatch(valid, { preauth_ref: "PA-PENDING", amount_kes: 800 });
    expect(next.preauth_ref).toBe("PA-PENDING");
    expect(next.amount_kes).toBe("800");
    expect(changedFields(valid, next).sort()).toEqual(["amount_kes", "preauth_ref"]);
  });

  it("applies a referral placeholder and keeps booleans as booleans", () => {
    const next = applyPatch(valid, { referral_ref: "REF-PENDING", emergency: true });
    expect(next.referral_ref).toBe("REF-PENDING");
    expect(next.emergency).toBe(true);
  });

  it("ignores keys that are not form fields", () => {
    expect(applyPatch(valid, { patient_token: "pat-1" })).toEqual(valid);
  });

  it("merges several patches with later ones winning", () => {
    expect(mergePatches([{ amount_kes: 1 }, { amount_kes: 2, preauth_ref: "PA-1" }])).toEqual({
      amount_kes: 2,
      preauth_ref: "PA-1",
    });
  });

  it("recognises an unchanged claim", () => {
    expect(sameClaim(valid, { ...valid })).toBe(true);
    expect(sameClaim(valid, { ...valid, amount_kes: "1" })).toBe(false);
  });
});

describe("todayIso", () => {
  it("formats the local date", () => {
    expect(todayIso(new Date(2026, 9, 19, 23, 30))).toBe("2026-10-19");
  });
});
