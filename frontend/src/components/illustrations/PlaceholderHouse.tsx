/** Placeholder when property has no image — house outline */
export default function PlaceholderHouse({ className = 'w-full h-full' }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center bg-slate-100 text-slate-300 ${className}`} aria-hidden>
      <svg viewBox="0 0 64 64" fill="none" className="w-2/3 h-2/3 max-w-[120px] max-h-[120px]">
        <path
          d="M32 8L8 28v28h16V44h16v12h16V28L32 8z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinejoin="round"
          fill="none"
        />
        <path d="M32 20v-4l-8 6v4l8-6z" fill="currentColor" fillOpacity="0.4" />
      </svg>
    </div>
  )
}
