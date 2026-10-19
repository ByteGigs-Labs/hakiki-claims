import { render, screen } from "@testing-library/react";
import { ActivityChart } from "./ActivityChart";
import { CauseBars } from "./CauseBars";

const daily = [
  { date: "2026-10-17", checks: 4, flagged: 1 },
  { date: "2026-10-18", checks: 0, flagged: 0 },
  { date: "2026-10-19", checks: 8, flagged: 8 },
];

describe("ActivityChart", () => {
  it("draws one bar per day and describes it for assistive tech", () => {
    render(<ActivityChart daily={daily} />);
    expect(screen.getByRole("list", { name: /claims checked per day/i })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
    expect(screen.getByTitle("19 Oct: 8 checked, 8 flagged")).toBeInTheDocument();
  });

  it("scales bars against the busiest day and the flagged share against each day", () => {
    render(<ActivityChart daily={daily} />);
    const days = screen.getAllByRole("listitem");
    expect(days[2]!.style.getPropertyValue("--h")).toBe("1");
    expect(days[0]!.style.getPropertyValue("--h")).toBe("0.5");
    expect(days[0]!.style.getPropertyValue("--f")).toBe("0.25");
    expect(days[1]!.style.getPropertyValue("--f")).toBe("0");
  });
});

describe("CauseBars", () => {
  it("lists each rule with its count", () => {
    render(<CauseBars rules={[{ rule: "R3", name: "Pre-authorisation", count: 6 }, { rule: "R6", name: "Tariff cap", count: 2 }]} />);
    expect(screen.getByText("Pre-authorisation")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getByText("Why claims fail")).toBeInTheDocument();
  });

  it("renders nothing when no rule is failing", () => {
    const { container } = render(<CauseBars rules={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
