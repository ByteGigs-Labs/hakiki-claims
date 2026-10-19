import { useEffect, useState } from "react";

interface Props {
  rules: { rule: string; name: string; count: number }[];
  title?: string;
}

export function CauseBars({ rules, title = "Why claims fail" }: Props) {
  const [armed, setArmed] = useState(false);
  const top = Math.max(...rules.map((rule) => rule.count), 1);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setArmed(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  if (rules.length === 0) return null;
  return (
    <div className="causes">
      <p className="eyebrow">{title}</p>
      <ul>
        {rules.map((rule, index) => (
          <li key={rule.rule} style={{ "--i": index } as React.CSSProperties}>
            <span className="causes__label">
              <b>{rule.rule}</b> {rule.name}
            </span>
            <span className="causes__track">
              <span className="causes__bar" style={{ width: armed ? `${(rule.count / top) * 100}%` : "0%" }} />
            </span>
            <span className="causes__count tabular">{rule.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
