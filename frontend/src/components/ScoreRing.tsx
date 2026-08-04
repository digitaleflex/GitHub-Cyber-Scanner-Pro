interface Props {
  score: number
  color?: string
  size?: number
}

export function ScoreRing({ score, color = 'var(--amber)', size = 160 }: Props) {
  const r = (size - 12) / 2
  const circ = 2 * Math.PI * r
  const pct = Math.min(score / 100, 1)

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth="8" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${pct * circ} ${circ}`}
          style={{ transition: 'stroke-dasharray 0.8s var(--ease-out)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-display">{score}</span>
        <span className="text-caption t-m">/ 100</span>
      </div>
    </div>
  )
}
