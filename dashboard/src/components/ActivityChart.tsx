import type { Overview } from "../types";

const SHORT_DATE = new Intl.DateTimeFormat("en-KE", { day: "numeric", month: "short" });
const label = (iso: string) => SHORT_DATE.format(new Date(`${iso}T00:00:00`));

export function ActivityChart({ daily }: { daily: Overview["daily"] }) {
  const peak = Math.max(...daily.map((day) => day.checks), 1);
  const stride = Math.max(Math.ceil(daily.length / 6), 1);
  return (
    <figure className="chart">
      <ol className="chart__bars" aria-label="Claims checked per day">
        {daily.map((day, index) => (
          <li
            key={day.date}
            className="chart__day"
            style={{ "--i": index, "--h": day.checks / peak, "--f": day.checks ? day.flagged / day.checks : 0 } as React.CSSProperties}
            title={`${label(day.date)}: ${day.checks} checked, ${day.flagged} flagged`}
          >
            <span className="chart__bar">
              <span className="chart__flag" />
            </span>
            <span className="chart__tick tabular">{index % stride === 0 ? label(day.date) : ""}</span>
          </li>
        ))}
      </ol>
      <figcaption className="chart__legend">
        <span>
          <i className="chart__key chart__key--clean" /> Checked
        </span>
        <span>
          <i className="chart__key chart__key--flag" /> Flagged
        </span>
      </figcaption>
    </figure>
  );
}
