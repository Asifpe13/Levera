const variantClasses: Record<string, string> = {
  success: 'bg-emerald-100 text-emerald-800',
  warning: 'bg-amber-100 text-amber-800',
  danger: 'bg-rose-100 text-rose-800',
  info: 'bg-sky-100 text-sky-800',
  accent: 'bg-indigo-100 text-indigo-800',
  neutral: 'bg-slate-100 text-slate-700',
  primary: 'bg-teal-100 text-teal-800',
}

interface BadgeProps {
  children: React.ReactNode
  variant?: keyof typeof variantClasses
  className?: string
}

export default function Badge({ children, variant = 'neutral', className = '' }: BadgeProps) {
  return (
    <span className={`levera-badge ${variantClasses[variant] || variantClasses.neutral} ${className}`}>
      {children}
    </span>
  )
}
