interface ScoreRingProps {
  score: number
  size?: number
  label?: string
}

export default function ScoreRing({ score, size = 56, label }: ScoreRingProps) {
  const clampedScore = Math.max(0, Math.min(100, score))
  const strokeWidth = 4
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference * (1 - clampedScore / 100)

  const color =
    clampedScore >= 70 ? 'text-emerald-500 stroke-emerald-500'
    : clampedScore >= 45 ? 'text-amber-500 stroke-amber-500'
    : 'text-rose-500 stroke-rose-500'

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" strokeWidth={strokeWidth}
          className="stroke-slate-200"
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          className={`${color} transition-all duration-500`}
        />
      </svg>
      <span className={`absolute text-sm font-bold ${color.split(' ')[0]}`} style={{ lineHeight: `${size}px`, width: size, textAlign: 'center', display: 'block', position: 'relative', top: -size - 4 }}>
        {clampedScore}
      </span>
      {label && <span className="text-xs text-slate-500 font-medium">{label}</span>}
    </div>
  )
}
