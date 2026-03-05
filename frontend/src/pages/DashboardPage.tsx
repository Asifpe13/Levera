import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import TabSettings from '../components/TabSettings'
import TabDeals from '../components/TabDeals'
import TabTrends from '../components/TabTrends'
import TabProfiles from '../components/TabProfiles'
import TabAlerts from '../components/TabAlerts'
import { AgentIcon } from '../components/illustrations'
import { INITIAL_NOTIFICATIONS, PROFILE_DEFINITIONS, type ProfileType } from '../levereConfig'

type TabId = 'deals' | 'profiles' | 'alerts' | 'settings' | 'trends'

const TABS: { id: TabId; label: string }[] = [
  { id: 'deals', label: 'דירות חיות' },
  { id: 'profiles', label: 'פרופילים' },
  { id: 'alerts', label: 'התראות' },
  { id: 'settings', label: 'הגדרות' },
  { id: 'trends', label: 'מגמות שוק' },
]

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState<TabId>('deals')
  const [activeProfileId, setActiveProfileId] = useState<ProfileType>('HOME_BUYER')
  const [notifications, setNotifications] = useState(INITIAL_NOTIFICATIONS)

  if (!user) return null

  const name = user.name || user.email
  const initials = name ? name[0].toUpperCase() : '?'

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen flex bg-slate-200/60">
      {/* Sidebar - fixed width, clear surface */}
      <aside className="w-64 flex-shrink-0 bg-white border-l border-slate-200/80 flex flex-col p-6 shadow-lg shadow-slate-200/50">
        <div className="text-center mb-6">
          <div className="flex justify-center gap-2 items-center mb-3">
            <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-600 flex items-center justify-center shrink-0">
              <AgentIcon className="w-6 h-6" />
            </div>
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-500 to-teal-700 text-white flex items-center justify-center text-xl font-bold shadow-lg shadow-teal-900/20">
              {initials}
            </div>
          </div>
          <div className="font-bold text-slate-800 text-lg">{name}</div>
          <div className="text-xs text-slate-500 mt-1">אימייל</div>
          <div className="text-sm text-slate-600 break-all mt-1 leading-relaxed">{user.email}</div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="mt-auto w-full py-3 px-4 rounded-xl font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-300 transition-colors"
        >
          התנתק
        </button>
      </aside>

      {/* Main - takes all remaining space, padded content */}
      <main className="flex-1 min-w-0 overflow-auto">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <nav className="flex gap-0 mb-8 bg-white/80 rounded-2xl p-1.5 shadow-sm border border-slate-200/80">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`flex-1 px-6 py-3 rounded-xl text-sm font-semibold transition-all ${
                  tab === t.id
                    ? 'bg-teal-600 text-white shadow-md shadow-teal-900/20'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>

          <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-200/80 p-8 min-h-[480px]">
            {tab === 'deals' && <TabDeals user={user} />}
            {tab === 'profiles' && (
              <TabProfiles
                user={user}
                profiles={PROFILE_DEFINITIONS}
                activeProfileId={activeProfileId}
                onChangeActiveProfile={setActiveProfileId}
              />
            )}
            {tab === 'alerts' && (
              <TabAlerts
                items={notifications}
                onUpdateItems={setNotifications}
              />
            )}
            {tab === 'settings' && <TabSettings user={user} />}
            {tab === 'trends' && <TabTrends />}
          </div>

          <footer className="mt-8 text-center text-sm text-slate-500">
            <span>Levera © 2026</span>
            <span className="mx-2">·</span>
            <span className="text-slate-600 font-medium">Asif Perets</span>
          </footer>
        </div>
      </main>
    </div>
  )
}
