export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="logo">
      <svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true">
        <path
          className="logo__frame"
          d="M24 5 8 13v22l16 8 16-8V13Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinejoin="round"
        />
        <path
          className="logo__core"
          d="M8 13l16 8 16-8M24 21v22"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {!compact && <span className="logo__word">Hakiki</span>}
    </span>
  );
}
