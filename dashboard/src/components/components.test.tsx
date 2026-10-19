import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import type { CheckResult, Fix, TraceStep } from "../types";
import { Dropzone } from "./Dropzone";
import { FixList } from "./FixList";
import { TraceTimeline } from "./TraceTimeline";
import { VerdictBanner } from "./VerdictBanner";
import { VerdictMark } from "./VerdictMark";

vi.mock("../lib/api", () => ({
  fetchReference: () => Promise.resolve({ rules: [{ id: "R3", name: "Pre-authorisation" }] }),
}));

const fix: Fix = {
  action: "Attach the pre-authorisation reference",
  action_sw: "Ambatisha nambari ya idhini ya awali",
  flips_to: "PASS",
  rule: "R3",
  patch: { preauth_ref: "PA-PENDING" },
  requires_input: true,
};

describe("FixList", () => {
  it("shows the action and applies it", async () => {
    const onApply = vi.fn();
    render(<FixList fixes={[fix]} language="en" busy={false} onApply={onApply} onApplyAll={vi.fn()} />);
    expect(screen.getByText(fix.action)).toBeInTheDocument();
    expect(screen.getByText(/enter the real value afterwards/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /apply/i }));
    expect(onApply).toHaveBeenCalledWith(fix);
  });

  it("switches to Swahili and offers apply-all for several fixes", () => {
    render(<FixList fixes={[fix, { ...fix, rule: "R6" }]} language="sw" busy={false} onApply={vi.fn()} onApplyAll={vi.fn()} />);
    expect(screen.getAllByText(fix.action_sw)).toHaveLength(2);
    expect(screen.getByRole("button", { name: /apply all/i })).toBeInTheDocument();
  });

  it("disables actions while a check is running", () => {
    render(<FixList fixes={[fix]} language="en" busy onApply={vi.fn()} onApplyAll={vi.fn()} />);
    expect(screen.getByRole("button", { name: /apply/i })).toBeDisabled();
  });
});

describe("Dropzone", () => {
  const file = (name: string) => new File(["a,b\n1,2\n"], name, { type: "text/csv" });

  it("passes a valid csv to the handler", async () => {
    const onFile = vi.fn();
    render(<Dropzone disabled={false} onFile={onFile} />);
    await userEvent.upload(screen.getByLabelText(/drop your claims file/i, { selector: "input" }), file("claims.csv"));
    expect(onFile).toHaveBeenCalledTimes(1);
  });

  it("explains why a file was refused", async () => {
    const onFile = vi.fn();
    render(<Dropzone disabled={false} onFile={onFile} />);
    const input = document.querySelector("input[type=file]") as HTMLInputElement;
    await userEvent.upload(input, file("claims.txt"), { applyAccept: false });
    expect(onFile).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("Choose a .csv file");
  });
});

describe("TraceTimeline", () => {
  const steps: TraceStep[] = [
    { step: 1, rule: "R3-Preauthorisation", result: "fail", fact: "Service requires pre-authorisation.", reason: "missing", values: {}, stv: [0.95, 0.92], citation: "kb/citations.json#R3" },
    { step: 2, rule: "R5-FacilityLevel", result: "skip", fact: "Not evaluated.", reason: "unknown_facility", values: {}, citation: "kb/citations.json#R5" },
  ];

  it("renders every step with its outcome and truth value", async () => {
    render(<TraceTimeline steps={steps} onCite={vi.fn()} />);
    expect(await screen.findByText("Pre-authorisation")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText("Not evaluated", { selector: ".trace__result" })).toBeInTheDocument();
    expect(screen.getByText("95% · 92%")).toBeInTheDocument();
  });

  it("opens the source for the rule that was clicked", async () => {
    const onCite = vi.fn();
    render(<TraceTimeline steps={steps} onCite={onCite} />);
    await userEvent.click(screen.getByRole("button", { name: /source r3/i }));
    expect(onCite).toHaveBeenCalledWith("R3");
  });

  it("renders text as text and never as markup", () => {
    const hostile: TraceStep[] = [{ ...steps[0]!, fact: "<img src=x onerror=alert(1)>" }];
    const { container } = render(<TraceTimeline steps={hostile} onCite={vi.fn()} />);
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
  });
});

describe("verdict visuals", () => {
  const result: CheckResult = {
    claim: "clm-104",
    verdict: "WILL_FAIL",
    truth_value: { strength: 0.95, confidence: 0.92 },
    revenue_at_risk_kes: 45000,
    trace: [],
    fixes: [],
    rulebook_version: "sha-rules-2026.10.0",
    trace_hash: "sha256:abc",
    prev_hash: "sha256:def",
  };

  it("announces the verdict in words, not just colour or shape", () => {
    render(<VerdictBanner result={result} />);
    expect(screen.getByText("Will fail")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "will fail" })).toBeInTheDocument();
    expect(screen.getByText("Fix before submitting")).toBeInTheDocument();
  });

  it.each(["PASS", "AT_RISK", "WILL_FAIL"] as const)("labels the %s mark", (verdict) => {
    render(<VerdictMark verdict={verdict} />);
    expect(screen.getByRole("img")).toHaveAttribute("aria-label", verdict.replace("_", " ").toLowerCase());
  });
});
