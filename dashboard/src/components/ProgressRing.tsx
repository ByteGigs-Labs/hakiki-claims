const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function ProgressRing({ fraction, label, caption }: { fraction: number; label: string; caption: string }) {
  const clamped = Math.min(Math.max(fraction, 0), 1);
  return (
    <figure className="ring" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(clamped * 100)}>
      <svg viewBox="0 0 128 128" width="128" height="128">
        <circle className="ring__track" cx="64" cy="64" r={RADIUS} />
        <circle
          className="ring__bar"
          cx="64"
          cy="64"
          r={RADIUS}
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE * (1 - clamped)}
        />
      </svg>
      <figcaption>
        <strong className="tabular">{label}</strong>
        <span>{caption}</span>
      </figcaption>
    </figure>
  );
}
