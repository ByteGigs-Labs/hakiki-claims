import { kes, percent, ruleId, ruleName, shortHash } from "./format";

describe("format", () => {
  it("formats money with thousands separators", () => {
    expect(kes(45000)).toBe("KES 45,000");
    expect(kes(1234.6)).toBe("KES 1,235");
  });

  it("shortens hashes without the algorithm prefix", () => {
    expect(shortHash("sha256:" + "a".repeat(20) + "b".repeat(44))).toBe("aaaaaaaa…bbbbbb");
  });

  it("splits trace rule labels", () => {
    expect(ruleId("R3-Preauthorisation")).toBe("R3");
    expect(ruleName("R2-FacilityContract")).toBe("Facility Contract");
  });

  it("rounds truth values to whole percents", () => {
    expect(percent(0.956)).toBe("96%");
  });
});
