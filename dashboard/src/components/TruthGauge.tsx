import { useCountUp } from "../hooks/useCountUp";
import { percent } from "../lib/format";

const RADIUS_OUTER = 62;
const RADIUS_INNER = 48;
const arc = (radius: number) => 2 * Math.PI * radius;

interface Props {
  strength: number;
  confidence: number;
  label: string;
}

function Arc({ radius, value, thin }: { radius: number; value: number; thin?: boolean }) {
  const length = arc(radius);
  return (
    <circle
      key={value}
      className={`gauge__bar${thin ? " gauge__bar--thin" : ""}`}
      cx="75"
      cy="75"
      r={radius}
      strokeDasharray={length}
      strokeDashoffset={length * (1 - value)}
      style={{ "--full": length } as React.CSSProperties}
    />
  );
}

export function TruthGauge({ strength, confidence, label }: Props) {
  const shown = useCountUp(strength * 100, 1200);
  return (
    <figure className="gauge" aria-label={`${label}: strength ${percent(strength)}, confidence ${percent(confidence)}`}>
      <svg viewBox="0 0 150 150" width="150" height="150">
        <circle className="gauge__track" cx="75" cy="75" r={RADIUS_OUTER} />
        <Arc radius={RADIUS_OUTER} value={strength} />
        <circle className="gauge__track gauge__track--thin" cx="75" cy="75" r={RADIUS_INNER} />
        <Arc radius={RADIUS_INNER} value={confidence} thin />
      </svg>
      <figcaption>
        <strong className="tabular">{Math.round(shown)}</strong>
        <span>{label}</span>
      </figcaption>
    </figure>
  );
}
