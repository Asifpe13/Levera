export default function HeroRealEstate(props: { className?: string }) {
  const { className = 'w-24 h-24' } = props
  return (
    <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden>
      <circle cx="60" cy="60" r="54" fill="#f0fdfa" />
      <path
        d="M60 28L32 48v44h20V62h16v30h20V48L60 28z"
        fill="#0d9488"
        stroke="#0f766e"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M60 38v-6l-12 8v6l12-8z" fill="rgba(255,255,255,0.4)" />
      <circle cx="82" cy="62" r="6" fill="none" stroke="#0d9488" strokeWidth="2" />
      <circle cx="82" cy="62" r="2.5" fill="#0d9488" />
      <path d="M88 62h8v4h-4v2h-4v-6z" fill="none" stroke="#0d9488" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="42" cy="42" r="2.5" fill="#14b8a6" opacity="0.9" />
      <circle cx="78" cy="38" r="2" fill="#14b8a6" opacity="0.7" />
      <circle cx="50" cy="72" r="1.5" fill="#14b8a6" opacity="0.6" />
    </svg>
  )
}
