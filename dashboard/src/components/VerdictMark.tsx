import { useId } from "react";
import type { Verdict } from "../types";

interface Props {
  verdict: Verdict;
  size?: number;
  animate?: boolean;
}

export function VerdictMark({ verdict, size = 96, animate = true }: Props) {
  const id = useId();
  return (
    <svg
      className={`verdict-mark verdict-mark--${verdict.toLowerCase()}${animate ? " is-animated" : ""}`}
      width={size}
      height={size}
      viewBox="0 0 96 96"
      role="img"
      aria-label={verdict.replace("_", " ").toLowerCase()}
    >
      <defs>
        <pattern id={`${id}-hatch`} width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="7" height="7" fill="none" />
          <rect width="2.6" height="7" fill="currentColor" />
        </pattern>
        <clipPath id={`${id}-half`}>
          <rect x="0" y="48" width="96" height="48" />
        </clipPath>
      </defs>
      {verdict === "PASS" && (
        <>
          <circle className="verdict-mark__disc" cx="48" cy="48" r="44" fill="currentColor" />
          <path className="verdict-mark__glyph" d="m28 50 14 14 27-31" />
        </>
      )}
      {verdict === "AT_RISK" && (
        <>
          <circle cx="48" cy="48" r="44" fill="none" stroke="currentColor" strokeWidth="3" className="verdict-mark__ring" />
          <circle cx="48" cy="48" r="44" fill="currentColor" clipPath={`url(#${id}-half)`} className="verdict-mark__disc" />
          <path className="verdict-mark__glyph verdict-mark__glyph--invert" d="M48 26v28M48 68v.5" />
        </>
      )}
      {verdict === "WILL_FAIL" && (
        <>
          <circle cx="48" cy="48" r="44" fill={`url(#${id}-hatch)`} className="verdict-mark__disc" />
          <circle cx="48" cy="48" r="44" fill="none" stroke="currentColor" strokeWidth="3" className="verdict-mark__ring" />
          <circle cx="48" cy="48" r="23" className="verdict-mark__plate" />
          <path className="verdict-mark__glyph" d="m38 38 20 20M58 38 38 58" />
        </>
      )}
    </svg>
  );
}
