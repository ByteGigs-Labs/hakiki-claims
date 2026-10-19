export function GlassCube({ className = "" }: { className?: string }) {
  return (
    <svg className={`glass-cube ${className}`} viewBox="0 0 400 400" aria-hidden="true">
      <defs>
        <linearGradient id="cube-top" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="currentColor" stopOpacity="0.16" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <g className="glass-cube__shape" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round">
        <path className="glass-cube__face" d="M200 50 340 125v150L200 350 60 275V125Z" fill="url(#cube-top)" />
        <path className="glass-cube__edge" pathLength="1" d="M60 125 200 200 340 125" />
        <path className="glass-cube__edge" pathLength="1" d="M200 200v150" />
        <path className="glass-cube__edge glass-cube__edge--inner" pathLength="1" d="M130 162 270 238M270 162 130 238M200 125v150" />
        <circle className="glass-cube__dot glass-cube__dot--a" cx="200" cy="200" r="7" fill="currentColor" stroke="none" />
        <circle className="glass-cube__dot glass-cube__dot--b" cx="130" cy="162" r="5" fill="currentColor" stroke="none" />
        <circle className="glass-cube__dot glass-cube__dot--c" cx="270" cy="238" r="5" fill="currentColor" stroke="none" />
      </g>
    </svg>
  );
}
