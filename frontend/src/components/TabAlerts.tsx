import { useMemo, useState } from 'react'
import type { NotificationItem } from '../levereConfig'
import { Badge } from './ui'

interface TabAlertsProps {
  items: NotificationItem[]
  onUpdateItems?: (items: NotificationItem[]) => void
}

const typeLabels: Record<NotificationItem['type'], string> = {
  match: 'התאמות חדשות',
  scan: 'סריקות',
  weekly: 'דוחות שבועיים',
  system: 'מערכת',
}

export default function TabAlerts({ items, onUpdateItems }: TabAlertsProps) {
  const [filterType, setFilterType] = useState<'all' | NotificationItem['type']>('all')
  const [filterRead, setFilterRead] = useState<'all' | 'read' | 'unread'>('all')
  const [search, setSearch] = useState('')

  const list = useMemo(() => {
    return items.filter((n) => {
      if (filterType !== 'all' && n.type !== filterType) return false
      if (filterRead === 'read' && !n.read) return false
      if (filterRead === 'unread' && n.read) return false
      const q = search.trim().toLowerCase()
      if (!q) return true
      return (
        n.title.toLowerCase().includes(q) ||
        n.message.toLowerCase().includes(q)
      )
    })
  }, [items, filterType, filterRead, search])

  function updateList(next: NotificationItem[]) {
    onUpdateItems?.(next)
  }

  function toggleRead(id: string) {
    updateList(items.map((n) => (n.id === id ? { ...n, read: !n.read } : n)))
  }

  function markAllRead() {
    updateList(items.map((n) => ({ ...n, read: true })))
  }

  function clearRead() {
    updateList(items.filter((n) => !n.read))
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 mb-1">התראות ופעילות הסוכן</h2>
          <p className="text-sm text-slate-600">
            כאן תראה כל התראה שהסוכן שלח — התאמות חדשות, סריקות שבוצעו ודוחות שבועיים.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <button
            type="button"
            onClick={markAllRead}
            className="levera-btn levera-btn-secondary px-3 py-1.5"
          >
            סמן הכל כנקרא
          </button>
          <button
            type="button"
            onClick={clearRead}
            className="levera-btn levera-btn-secondary px-3 py-1.5"
          >
            נקה התראות שנקראו
          </button>
        </div>
      </header>

      <section className="levera-card p-4 space-y-3">
        <div className="grid md:grid-cols-[minmax(0,2fr)_minmax(0,1.2fr)] gap-3 text-xs">
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-slate-500 font-semibold text-[11px]">סינון לפי סוג:</span>
            <button
              type="button"
              onClick={() => setFilterType('all')}
              className={`levera-badge cursor-pointer ${
                filterType === 'all' ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-700'
              }`}
            >
              הכל
            </button>
            {(['match', 'scan', 'weekly', 'system'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setFilterType(t)}
                className={`levera-badge cursor-pointer ${
                  filterType === t ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-700'
                }`}
              >
                {typeLabels[t]}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-2 items-center justify-start md:justify-end">
            <span className="text-slate-500 font-semibold text-[11px]">סטטוס:</span>
            {(['all', 'unread', 'read'] as const).map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setFilterRead(v)}
                className={`levera-badge cursor-pointer ${
                  filterRead === v ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'
                }`}
              >
                {v === 'all' ? 'הכל' : v === 'unread' ? 'לא נקראו' : 'נקראו'}
              </button>
            ))}
          </div>
        </div>
        <div>
          <input
            className="levera-input text-xs md:text-sm"
            placeholder="סינון לפי טקסט בהתראה (עיר, מחיר, סוג עסקה...)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </section>

      <section className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
          <span>
            מציג {list.length} מתוך {items.length} התראות
          </span>
        </div>
        {list.length === 0 ? (
          <div className="levera-card p-6 text-sm text-slate-600 text-center">
            עדיין אין התראות מתאימות לסינון שבחרת. ברגע שהסוכן ימצא דירות חדשות — הן יופיעו כאן
            וגם במייל שלך.
          </div>
        ) : (
          <div className="space-y-2">
            {list.map((n) => {
              const date = new Date(n.createdAt)
              const timeLabel = isNaN(date.getTime())
                ? ''
                : date.toLocaleString('he-IL', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })
              return (
                <article
                  key={n.id}
                  className={`levera-card px-4 py-3 text-xs md:text-sm flex flex-col gap-1 border-r-4 ${
                    n.read ? 'border-slate-200 bg-white' : 'border-teal-500 bg-teal-50/60'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-800">{n.title}</span>
                      <Badge
                        variant={
                          n.type === 'match'
                            ? 'success'
                            : n.type === 'weekly'
                            ? 'accent'
                            : n.type === 'scan'
                            ? 'info'
                            : 'neutral'
                        }
                      >
                        {typeLabels[n.type]}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {timeLabel && (
                        <span className="text-[11px] text-slate-500">{timeLabel}</span>
                      )}
                      <button
                        type="button"
                        onClick={() => toggleRead(n.id)}
                        className="text-[11px] text-teal-700 hover:text-teal-900 underline-offset-2 hover:underline"
                      >
                        {n.read ? 'סמן כלא נקרא' : 'סמן כנקרא'}
                      </button>
                    </div>
                  </div>
                  <p className="text-slate-600">{n.message}</p>
                </article>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}

