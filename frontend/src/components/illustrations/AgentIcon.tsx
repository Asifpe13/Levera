/** Compact icon: house + magnifying glass — smart agent search */
export default function AgentIcon({ className = 'w-12 h-12' }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden>
      <path
        d="M24 12L10 22v14h8V28h12v8h8V22L24 12z"
        fill="currentColor"
        className="text-teal-600"
        fillOpacity="0.9"
      />
      <circle cx="32" cy="32" r="8" stroke="currentColor" strokeWidth="2" className="text-teal-500" fill="none" />
      <path d="M36 36l6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="text-teal-500" />
    </svg>
  )
}
