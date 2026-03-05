type Verdict = 'BUY' | 'INVEST' | 'CONSIDER' | 'REJECT' | string

const verdictConfig: Record<string, { bg: string; text: string; label: string }> = {
  BUY:      { bg: 'bg-emerald-500', text: 'text-white', label: 'מומלץ לרכישה' },
  INVEST:   { bg: 'bg-indigo-500',  text: 'text-white', label: 'השקעה מומלצת' },
  CONSIDER: { bg: 'bg-amber-500',   text: 'text-white', label: 'שווה בדיקה' },
  REJECT:   { bg: 'bg-rose-500',    text: 'text-white', label: 'לא מומלץ' },
}

interface VerdictBannerProps {
  verdict: Verdict
  confidence?: number
  className?: string
}

export default function VerdictBanner({ verdict, confidence, className = '' }: VerdictBannerProps) {
  const cfg = verdictConfig[verdict] || verdictConfig.CONSIDER
  return (
    <div className={`${cfg.bg} ${cfg.text} rounded-xl px-4 py-2.5 flex items-center justify-between gap-3 font-semibold text-sm ${className}`}>
      <span>{cfg.label}</span>
      {confidence != null && (
        <span className="opacity-80 text-xs font-medium">ביטחון: {confidence}%</span>
      )}
    </div>
  )
}
