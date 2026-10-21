import axe from "axe-core";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { TraceTimeline } from "./components/TraceTimeline";
import { AccountPage } from "./pages/account";
import { KeysPage } from "./pages/keys";
import { TeamPage } from "./pages/team";
import type { TraceStep } from "./types";

vi.mock("@refinedev/core", () => ({ useGetIdentity: () => ({ data: { id: "u1", role: "admin" } }) }));
vi.mock("./lib/api", () => ({
  fetchUsers: () => Promise.resolve([{ id: "u2", name: "Wanjiru", email: "w@mercy.test", role: "clerk", is_active: true, created_at: "2026-10-01T08:00:00Z" }]),
  fetchApiKeys: () => Promise.resolve([{ id: "k1", name: "Billing", prefix: "ab12cd34", created_at: "2026-10-01T08:00:00Z", last_used_at: null, revoked_at: null }]),
  fetchReference: () => Promise.resolve({ rules: [{ id: "R3", name: "Pre-authorisation" }] }),
  fetchCitation: () => Promise.resolve({ metta_source: "(= (check-r3 $c) (Result R3 fail))" }),
  errorMessage: (_: unknown, fallback: string) => fallback,
}));

const audit = async (container: HTMLElement) => {
  const result = await axe.run(container, {
    runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
    rules: { "color-contrast": { enabled: false } },
  });
  return result.violations.map((violation) => `${violation.id}: ${violation.nodes.map((n) => n.target.join(" ")).join(", ")}`);
};

const step: TraceStep = {
  step: 1,
  rule: "R3-Preauthorisation",
  result: "fail",
  fact: "Service requires pre-authorisation.",
  reason: "missing",
  values: {},
  stv: [0.95, 0.92],
  citation: "kb/citations.json#R3",
  premises: ["(PreauthRequired svc-CS-01 SHIF)"],
};

describe("accessibility", () => {
  it("team page has no violations", async () => {
    const { container } = render(<TeamPage />);
    await screen.findByText("Wanjiru");
    expect(await audit(container)).toEqual([]);
  });

  it("api keys page has no violations", async () => {
    const { container } = render(<KeysPage />);
    await screen.findByText("hk_ab12cd34…");
    expect(await audit(container)).toEqual([]);
  });

  it("password page has no violations", async () => {
    const { container } = render(<AccountPage />);
    expect(await audit(container)).toEqual([]);
  });

  it("an open trace step has no violations and its code blocks can be reached by keyboard", async () => {
    const { container } = render(<TraceTimeline steps={[step]} onCite={vi.fn()} />);
    await userEvent.click(await screen.findByRole("button", { name: /show the logic/i }));
    await screen.findByText(/check-r3/);
    expect(await audit(container)).toEqual([]);
    expect(screen.getByLabelText("Matched facts")).toHaveAttribute("tabindex", "0");
  });
});
