import { useState, useEffect, useCallback } from 'react'
import type { User, Property } from '../api'
import { getProperties, runScan, requestWeeklyReport } from '../api'
import PropertyCard from './PropertyCard'
import { AgentIcon } from './illustrations'

const DEAL_OPTS = [
  { value: '', label: 'הכל' },
  { value: 'sale', label: 'מכירה' },
  { value: 'rent', label: 'שכירות' },
]

const pillBase = 'px-3 py-2 rounded-full text-sm font-medium transition-colors'
const pillActive = 'bg-teal-600 text-white'
const pillInactive = 'bg-slate-100 text-slate-600 hover:bg-slate-200'

export default function TabDeals({ user }: { user: User }) {
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [dealFilter, setDealFilter] = useState('')
  const [cityFilter, setCityFilter] = useState('')
  const [cities, setCities] = useState<string[]>([])
  const [scanning, setScanning] = useState(false)
  const [scanLog, setScanLog] = useState<{ time: string; level: string; message: string }[]>([])
  const [scanSummary, setScanSummary] = useState<{ total_found: number; total_matches: number } | null>(null)
  const [showLogDetail, setShowLogDetail] = useState(false)
  const [toast, setToast] = useState('')
  const [weeklyReportLoading, setWeeklyReportLoading] = useState(false)
  const [weeklyReportToast, setWeeklyReportToast] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const list = await getProperties({
        deal_type: dealFilter || undefined,
        city: cityFilter || undefined,
        limit: 50,
      })
      setProperties(list)
      const citySet = new Set(list.map((p) => (p.city || '').trim()).filter(Boolean))
      setCities(['הכל', ...Array.from(citySet).sort()])
    } finally {
      setLoading(false)
    }
  }, [dealFilter, cityFilter])

  useEffect(() => {
    load()
  }, [load])

  const filteredByCity =
    cityFilter && cityFilter !== 'הכל'
      ? properties.filter((p) => (p.city || '').trim() === cityFilter)
      : properties

  async function handleRunScan() {
    setScanning(true)
    setScanLog([])
    setScanSummary(null)
    setShowLogDetail(false)
    try {
      const res = await runScan()
      setScanLog(res.log)
      setScanSummary({ total_found: res.total_found, total_matches: res.total_matches })
      setToast('הסריקה הושלמה — ' + res.total_matches + ' התאמות חדשות')
      load()
    } catch (err) {
      setScanLog([{ time: '', level: 'error', message: err instanceof Error ? err.message : 'שגיאה' }])
      setScanSummary(null)
    } finally {
      setScanning(false)
    }
  }

  async function handleWeeklyReport() {
    setWeeklyReportToast('')
    setWeeklyReportLoading(true)
    try {
      const res = await requestWeeklyReport()
      if (res.ok) {
        setWeeklyReportToast(res.properties_count > 0 ? `הדוח השבועי נשלח למייל (${res.properties_count} דירות)` : 'הדוח השבועי נשלח למייל')
      } else {
        setWeeklyReportToast(res.message || 'שגיאה בהפקת הדוח')
      }
    } catch (err) {
      setWeeklyReportToast(err instanceof Error ? err.message : 'שגיאה בהפקת הדוח')
    } finally {
      setWeeklyReportLoading(false)
    }
  }

  const searchLabel =
    user.search_type === 'both' ? 'קנייה + שכירות' : user.search_type === 'buy' ? 'מכירה' : 'שכירות'
  const maxRepay = Math.round(user.monthly_income * user.max_repayment_ratio)

  return (
    <>
      <div className="bg-gradient-to-l from-teal-50 to-white rounded-2xl border-2 border-teal-100 shadow-md p-6 mb-6 flex flex-wrap gap-6 items-start">
        <div className="shrink-0 w-14 h-14 rounded-2xl bg-teal-100 text-teal-600 flex items-center justify-center">
          <AgentIcon className="w-8 h-8" />
        </div>
        <div className="min-w-0 flex-1">
        <h2 className="text-xl font-bold text-slate-800 mb-1">הסוכן של {user.name}</h2>
        <p className="text-slate-600 text-sm mb-5 leading-relaxed">
          סורק {user.target_cities?.length || 0} ערים · שולח התראות ל-{user.email} · סריקה אוטומטית כל שעה
        </p>
        <div className="flex flex-wrap gap-4">
          <div className="px-5 py-3 rounded-xl bg-white border border-slate-200 shadow-sm text-sm font-medium">
            <span className="font-semibold text-slate-800">{user.target_cities?.length || 0}</span>
            <span className="text-slate-600 mr-1">ערים</span>
          </div>
          <div className="px-5 py-3 rounded-xl bg-white border border-slate-200 shadow-sm text-sm font-medium">
            <span className="font-semibold text-slate-800">{maxRepay.toLocaleString()}₪</span>
            <span className="text-slate-600 mr-1">החזר מקסימלי</span>
          </div>
          <div className="px-5 py-3 rounded-xl bg-white border border-slate-200 shadow-sm text-sm font-medium">
            <span className="font-semibold text-slate-800">{user.equity?.toLocaleString()}₪</span>
            <span className="text-slate-600 mr-1">הון עצמי</span>
          </div>
          <div className="px-5 py-3 rounded-xl bg-white border border-slate-200 shadow-sm text-sm font-medium">
            <span className="font-semibold text-slate-800">{searchLabel}</span>
          </div>
        </div>
        </div>
      </div>
      <div className="mb-6 flex flex-wrap gap-3 items-center">
        <button
          type="button"
          onClick={handleRunScan}
          disabled={scanning}
          className="px-5 py-3 rounded-xl font-semibold text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-colors"
        >
          {scanning ? 'סורק...' : 'שלח את הסוכן לסרוק'}
        </button>
        <button
          type="button"
          onClick={handleWeeklyReport}
          disabled={weeklyReportLoading}
          className="px-5 py-3 rounded-xl font-semibold text-slate-700 bg-white border-2 border-teal-500 text-teal-700 hover:bg-teal-50 disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-colors"
        >
          {weeklyReportLoading ? 'מפיק דוח...' : 'הפק דוח שבועי עכשיו'}
        </button>
      </div>
      {weeklyReportToast && <p className="text-teal-600 font-medium mb-4">{weeklyReportToast}</p>}
      <p className="text-xs text-slate-500 mb-4">דוח שבועי נשלח אוטומטית גם כל חמישי ב־21:00 למייל שלך.</p>

      {/* תהליך הסריקה — מוצג בזמן סריקה ואחריה */}
      {(scanning || scanLog.length > 0) && (
        <div className="bg-white rounded-2xl border-2 border-teal-100 shadow-sm p-6 mb-6">
          <h3 className="text-base font-semibold text-slate-800 mb-4">
            {scanning ? 'הסוכן עובד עכשיו' : 'סיכום הסריקה'}
          </h3>
          {scanning ? (
            <ul className="text-slate-600 text-sm space-y-1.5 list-none">
              <li>• סורק אתרים (Yad2, Madlan וכו')</li>
              <li>• בודק התאמה להעדפות</li>
              <li>• מנתח עם AI ושומר התאמות</li>
            </ul>
          ) : scanSummary ? (
            <>
              <ul className="text-slate-600 text-sm space-y-1.5 mb-4 list-none">
                <li>• נסרקו {scanSummary.total_found} דירות</li>
                <li>• נשמרו {scanSummary.total_matches} התאמות חדשות</li>
              </ul>
              <button
                type="button"
                onClick={() => setShowLogDetail(!showLogDetail)}
                className="text-sm font-medium text-teal-600 hover:text-teal-700 focus:outline-none"
              >
                {showLogDetail ? 'הסתר פירוט' : 'הצג פירוט הלוג'}
              </button>
              {showLogDetail && (
                <div className="mt-3 p-4 rounded-xl bg-slate-50 border border-slate-200 max-h-56 overflow-auto font-mono text-xs text-slate-600">
                  {scanLog.map((line, i) => (
                    <div key={i} className={line.level === 'error' ? 'text-red-600' : ''}>
                      {line.time && <span className="text-slate-400 mr-2">{line.time}</span>}
                      {line.message}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="text-red-600 text-sm">
              {scanLog.map((l, i) => l.message).join(' ')}
            </div>
          )}
        </div>
      )}
      {toast && <p className="text-teal-600 font-medium mb-4">{toast}</p>}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 pb-4 border-b border-slate-200">
        <h3 className="text-lg font-semibold text-slate-800">דירות שנשמרו עבורך</h3>
        <span className="px-4 py-2 rounded-xl bg-teal-600 text-white text-sm font-semibold">
          {filteredByCity.length} דירות
        </span>
      </div>
      {properties.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-6">
          <div className="mb-4">
            <span className="block text-xs font-semibold text-slate-500 mb-2">סוג עסקה</span>
            <div className="flex flex-wrap gap-2">
              {DEAL_OPTS.map((o) => (
                <button
                  key={o.value || 'all'}
                  type="button"
                  onClick={() => setDealFilter(o.value)}
                  className={dealFilter === o.value ? `${pillBase} ${pillActive}` : `${pillBase} ${pillInactive}`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <span className="block text-xs font-semibold text-slate-500 mb-2">עיר</span>
            <div className="flex flex-wrap gap-2">
              {cities.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCityFilter(c)}
                  className={cityFilter === c ? `${pillBase} ${pillActive}` : `${pillBase} ${pillInactive}`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      <p className="text-sm text-slate-500 mb-4">מציג {filteredByCity.length} דירות</p>
      {loading ? (
        <p className="text-slate-500">טוען...</p>
      ) : filteredByCity.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">הסוכן ממתין לפקודה</h3>
          <p className="text-slate-600">לחץ על &quot;שלח את הסוכן לסרוק&quot; כדי שיחפש עבורך דירות</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredByCity.map((prop) => (
            <PropertyCard
              key={prop.id || prop.source_id || prop.listing_url || String(Math.random())}
              prop={prop}
            />
          ))}
        </div>
      )}
    </>
  )
}
