type TabId = 'deals' | 'profiles' | 'alerts' | 'settings' | 'trends'

interface Tab {
  id: TabId
  label: string
  icon: React.ReactNode
}

const TABS: Tab[] = [
  {
    id: 'deals',
    label: 'דירות',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5" aria-hidden>
        <path d="M3 10.5L12 3l9 7.5V21H3V10.5z" strokeLinejoin="round" />
        <path d="M9 21v-6h6v6" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    id: 'profiles',
    label: 'פרופילים',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5" aria-hidden>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4 3.5-7 8-7s8 3 8 7" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    id: 'alerts',
    label: 'התראות',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5" aria-hidden>
        <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" strokeLinejoin="round" />
        <path d="M13.7 21a2 2 0 01-3.4 0" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    id: 'trends',
    label: 'שוק',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5" aria-hidden>
        <path d="M3 17l6-6 4 4 8-10" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M17 5h4v4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    id: 'settings',
    label: 'הגדרות',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5" aria-hidden>
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" strokeLinecap="round" />
      </svg>
    ),
  },
]

interface MobileBottomNavProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
}

export default function MobileBottomNav({ activeTab, onTabChange }: MobileBottomNavProps) {
  return (
    <nav
      className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-200/80 safe-bottom"
      aria-label="ניווט ראשי"
    >
      <div className="flex items-stretch justify-around px-1 pt-1 pb-1">
        {TABS.map((tab) => {
          const active = activeTab === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onTabChange(tab.id)}
              className={`flex flex-col items-center justify-center gap-0.5 flex-1 py-2 px-1 rounded-lg transition-colors min-w-0 ${
                active ? 'text-teal-600' : 'text-slate-500 hover:text-slate-700'
              }`}
              aria-current={active ? 'page' : undefined}
            >
              <span className={active ? 'scale-110 transition-transform' : ''}>{tab.icon}</span>
              <span className={`text-[10px] font-semibold truncate w-full text-center ${active ? 'text-teal-700' : ''}`}>
                {tab.label}
              </span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}

export type { TabId }
