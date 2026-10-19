import { useEffect, useRef, useState } from "react";

const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export function useCountUp(target: number, duration = 1100) {
  const [value, setValue] = useState(0);
  const current = useRef(0);

  useEffect(() => {
    const from = current.current;
    const span = prefersReducedMotion() ? 0 : duration;
    const started = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const progress = span === 0 ? 1 : Math.min((now - started) / span, 1);
      const eased = 1 - Math.pow(1 - progress, 4);
      current.current = from + (target - from) * eased;
      setValue(current.current);
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);

  return value;
}
