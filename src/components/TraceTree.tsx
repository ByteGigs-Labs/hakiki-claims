import { Tag, Timeline, Typography } from "antd";
import type { TraceStep, Verdict } from "../types";

const { Text } = Typography;

const verdictColor: Record<Verdict, string> = {
  PASS: "green",
  AT_RISK: "orange",
  WILL_FAIL: "red",
};

const stepColor = { pass: "green", warn: "orange", fail: "red" } as const;

export const VerdictTag = ({ verdict }: { verdict: Verdict }) => (
  <Tag color={verdictColor[verdict]}>{verdict.replace("_", " ")}</Tag>
);

// All values render as React text nodes — never as HTML.
export const TraceTree = ({ steps }: { steps: TraceStep[] }) => (
  <Timeline
    items={steps.map((s) => ({
      color: stepColor[s.result],
      children: (
        <div>
          <Text strong>
            {s.step}. {s.rule}
          </Text>{" "}
          <Tag color={stepColor[s.result]}>{s.result}</Tag>
          {s.stv && (
            <Text type="secondary">
              stv ({s.stv[0].toFixed(2)}, {s.stv[1].toFixed(2)})
            </Text>
          )}
          <div>{s.fact}</div>
          {s.citation && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              Source: {s.citation}
            </Text>
          )}
        </div>
      ),
    }))}
  />
);
