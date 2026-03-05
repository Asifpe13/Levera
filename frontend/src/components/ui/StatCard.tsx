interface StatCardProps {
  value: string | number
  label: string
  icon?: React.ReactNode
  accent?: boolean
}

export default function StatCard({ value, label, icon, accent }: StatCardProps) {
  return (
    <div className={`levera-card px-5 py-4 flex items-center gap-3 min-w-[140px] ${accent ? 'border-teal-200 bg-teal-50/40' : ''}`}>
      {icon && <div className="shrink-0 w-10 h-10 rounded-xl bg-teal-100 text-teal-600 flex items-center justify-center">{icon}</div>}
      <div>
        <div className="text-xl font-bold text-slate-800 leading-tight">{value}</div>
        <div className="text-xs text-slate-500 mt-0.5">{label}</div>
      </div>
    </div>
  )
}
