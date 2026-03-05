/** Empty state: house + chart — for no data yet */
export default function EmptyCharts({ className = 'w-28 h-28' }: { className?: string }) {
  return (
    <svg viewBox="0 0 112 112" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden>
      <circle cx="56" cy="56" r="50" fill="#f0fdfa" />
      <path d="M56 36L38 50v26h12V58h12v18h12V50L56 36z" fill="#99f6e4" stroke="#14b8a6" strokeWidth="1.2" strokeLinejoin="round" />
      <path d="M72 70v12h-6V70h6z" fill="#5eead4" rx="1" />
      <path d="M80 64v18h-6V64h6z" fill="#2dd4bf" rx="1" />
      <path d="M88 58v24h-6V58h6z" fill="#14b8a6" rx="1" />
      <path d="M66 76v6h-6v-6h6z" fill="#99f6e4" rx="1" />
      <path d="M74 72v10h-6V72h6z" fill="#5eead4" rx="1" />
      <path d="M82 66v16h-6V66h6z" fill="#2dd4bf" rx="1" />
    </svg>
  )
}
