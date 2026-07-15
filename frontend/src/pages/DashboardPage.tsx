import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { getNotifications, markNotificationsRead, deleteReadNotifications, type AppNotification } from '../api'
import TabSettings from '../components/TabSettings'
import TabDeals from '../components/TabDeals'
import TabTrends from '../components/TabTrends'
import TabProfiles from '../components/TabProfiles'
import TabAlerts from '../components/TabAlerts'
import { AgentIcon } from '../components/illustrations'
import MobileBottomNav, { type TabId } from '../components/MobileBottomNav'
import { PROFILE_DEFINITIONS, type ProfileType } from '../levereConfig'

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
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [notificationsLoading, setNotificationsLoading] = useState(false)

  const refreshNotifications = useCallback(async () => {
    setNotificationsLoading(true)
    try {
      const items = await getNotifications({ limit: 100 })
      setNotifications(items)
    } catch {
      setNotifications([])
    } finally {
      setNotificationsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (user) refreshNotifications()
  }, [user, refreshNotifications])

  async function handleUpdateNotifications(next: AppNotification[]) {
    const prev = notifications

    if (next.length < prev.length) {
      setNotifications(next)
      await deleteReadNotifications().catch(() => refreshNotifications())
      return
    }

    const allRead = next.length > 0 && next.every((n) => n.read)
    const hadUnread = prev.some((n) => !n.read)
    if (allRead && hadUnread && next.length === prev.length) {
      setNotifications(next)
      await markNotificationsRead({ mark_all: true, read: true }).catch(() => refreshNotifications())
      return
    }

    setNotifications(next)
    const changed = next.filter((n) => {
      const old = prev.find((p) => p.id === n.id)
      return old && old.read !== n.read
    })
    if (changed.length) {
      await markNotificationsRead({
        ids: changed.map((n) => n.id),
        read: changed[0].read,
      }).catch(() => refreshNotifications())
    }
  }

  if (!user) return null

  const name = user.name || user.email
  const initials = name ? name[0].toUpperCase() : '?'

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-200/60">
      {/* Mobile topbar */}
      <header className="md:hidden w-full bg-white border-b border-slate-200/80 px-4 py-3 flex items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500 to-teal-700 text-white flex items-center justify-center text-base font-bold shadow flex-shrink-0">
            {initials}
          </div>
          <div className="min-w-0">
            <div className="font-semibold text-slate-800 text-sm truncate">{name}</div>
            <div className="text-[11px] text-slate-500 truncate">{user.email}</div>
          </div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="flex-shrink-0 py-1.5 px-3 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
        >
          התנתק
        </button>
      </header>

      {/* Sidebar - desktop only */}
      <aside className="hidden md:flex w-64 flex-shrink-0 bg-white border-l border-slate-200/80 flex-col p-6 shadow-lg shadow-slate-200/50">
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

      {/* Main content */}
      <main className="flex-1 min-w-0 overflow-auto pb-20 md:pb-0">
        <div className="w-full max-w-5xl mx-auto px-3 sm:px-6 py-4 sm:py-8">
          {/* Tabs nav – desktop only; mobile uses bottom navigation */}
          <nav className="hidden md:flex gap-0 mb-6 bg-white/80 rounded-xl sm:rounded-2xl p-1 sm:p-1.5 shadow-sm border border-slate-200/80 overflow-x-auto">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`flex-shrink-0 flex-1 min-w-[4.5rem] px-3 sm:px-6 py-2 sm:py-3 rounded-lg sm:rounded-xl text-xs sm:text-sm font-semibold transition-all whitespace-nowrap ${
                  tab === t.id
                    ? 'bg-teal-600 text-white shadow-md shadow-teal-900/20'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>

          <div className="bg-white rounded-xl sm:rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-200/80 p-4 sm:p-8 min-h-[400px]">
            {tab === 'deals' && <TabDeals user={user} onGoToSettings={() => setTab('settings')} />}
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
                loading={notificationsLoading}
                onUpdateItems={handleUpdateNotifications}
                onRefresh={refreshNotifications}
              />
            )}
            {tab === 'settings' && <TabSettings user={user} />}
            {tab === 'trends' && <TabTrends />}
          </div>

          <footer className="mt-6 mb-2 md:mb-0 text-center text-xs sm:text-sm text-slate-500">
            <span>Levera © 2026</span>
            <span className="mx-2">·</span>
            <span className="text-slate-600 font-medium">Asif Perets</span>
          </footer>
        </div>
      </main>

      <MobileBottomNav activeTab={tab} onTabChange={setTab} />
    </div>
  )
}
