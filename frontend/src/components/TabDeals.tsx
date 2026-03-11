import { useState, useEffect, useCallback, useRef } from 'react'
import type { User, Property, ScanStatus, ScanRejections } from '../api'
import { getProperties, startScan, getScanStatus, requestWeeklyReport } from '../api'
import PropertyCard from './PropertyCard'
import { AgentIcon } from './illustrations'

type ViewMode = 'latest' | 'all'

const DEAL_OPTS = [
  { value: '', label: 'הכל' },
  { value: 'sale', label: 'מכירה' },
  { value: 'rent', label: 'שכירות' },
]

const pillBase = 'px-3 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap'
const pillActive = 'bg-teal-600 text-white'
const pillInactive = 'bg-slate-100 text-slate-600 hover:bg-slate-200'

const LOG_LEVEL_CLASS: Record<string, string> = {
  success: 'text-teal-400',
  error: 'text-red-400',
  warn: 'text-yellow-400',
  info: 'text-slate-300',
}

// ---------------------------------------------------------------------------
// Rejection breakdown panel
// ---------------------------------------------------------------------------

function RejectionBreakdown({
  total,
  rejections,
}: {
  total: number
  rejections: ScanRejections
}) {
  const rows: { label: string; count: number; color: string }[] = [
    {
      label: 'דירות נפסלו עקב החזר חודשי גבוה מהגדרתך',
      count: (rejections.high_mortgage ?? 0) + (rejections.over_budget ?? 0),
      color: 'text-yellow-400',
    },
    {
      label: 'דירות נפסלו עקב מודעות חשודות או לא אמינות',
      count: rejections.suspicious ?? 0,
      color: 'text-orange-400',
    },
    {
      label: 'דירות נפסלו עקב חוסר רלוונטיות (שותפים, מחסנים וכדומה)',
      count: (rejections.irrelevant ?? 0) + (rejections.low_score ?? 0),
      color: 'text-slate-400',
    },
    {
      label: 'דירות נפסלו עקב מספר חדרים או סיבות אחרות',
      count: (rejections.wrong_rooms ?? 0) + (rejections.other ?? 0),
      color: 'text-slate-500',
    },
  ].filter((r) => r.count > 0)

  if (rows.length === 0) return null

  return (
    <div className="mx-4 mb-4 rounded-xl bg-slate-800/60 border border-slate-700 px-4 py-3 space-y-2">
      <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-1">
        פירוט סינון
      </p>
      <div className="font-mono text-xs text-teal-300">
        {total} דירות נמצאו בסריקה הטכנית
      </div>
      {rows.map((r) => (
        <div key={r.label} className={`font-mono text-xs ${r.color} flex gap-2`}>
          <span className="shrink-0">{r.count}</span>
          <span>{r.label}</span>
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------

export default function TabDeals({ user }: { user: User }) {
  const [viewMode, setViewMode] = useState<ViewMode>('latest')
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [dealFilter, setDealFilter] = useState('')
  const [cityFilter, setCityFilter] = useState('')
  const [cities, setCities] = useState<string[]>([])

  // Scan state
  const [scanning, setScanning] = useState(false)
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null)
  const [showLog, setShowLog] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const logBoxRef = useRef<HTMLDivElement>(null)

  // Toast state
  const [toast, setToast] = useState('')
  const [weeklyReportLoading, setWeeklyReportLoading] = useState(false)
  const [weeklyReportToast, setWeeklyReportToast] = useState('')

  const load = useCallback(async (mode: ViewMode = viewMode) => {
    setLoading(true)
    try {
      const list = await getProperties({
        deal_type: dealFilter || undefined,
        city: cityFilter || undefined,
        limit: 50,
        view: mode,
      })
      setProperties(list)
      const citySet = new Set(list.map((p) => (p.city || '').trim()).filter(Boolean))
      setCities(['הכל', ...Array.from(citySet).sort()])
    } finally {
      setLoading(false)
    }
  }, [dealFilter, cityFilter, viewMode])

  useEffect(() => {
    load(viewMode)
  }, [load, viewMode])

  // Auto-scroll log to bottom when new lines arrive
  useEffect(() => {
    if (logBoxRef.current) {
      logBoxRef.current.scrollTop = logBoxRef.current.scrollHeight
    }
  }, [scanStatus?.log?.length])

  // Cleanup poll on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const filteredByCity =
    cityFilter && cityFilter !== 'הכל'
      ? properties.filter((p) => (p.city || '').trim() === cityFilter)
      : properties

  // ------------------------------------------------------------------
  // Scan with live status polling
  // ------------------------------------------------------------------

  async function handleRunScan() {
    if (scanning) return

    setScanning(true)
    setScanStatus(null)
    setShowLog(false)
    setToast('')

    // Attempt to start the scan, but DO NOT stop if it times out.
    // On Render free-tier the cold-start can exceed 60 s; the backend
    // likely received the request and queued the background task even
    // when the client never sees the response.
    let hardError = false
    try {
      await startScan()
    } catch (err) {
      const msg = err instanceof Error ? err.message : ''
      const isTimeout =
        msg.includes('יותר מדי זמן') ||
        msg.toLowerCase().includes('timeout') ||
        msg.toLowerCase().includes('abort')

      if (isTimeout) {
        // Backend probably started — begin polling to confirm
        setScanStatus((prev) => prev ?? {
          running: true,
          finished: false,
          message: 'מחכה לתגובת השרת... (האתחול עשוי לקחת עד דקה)',
          total_found: 0,
          total_matches: 0,
          log: [],
        })
      } else {
        // Definitive failure (4xx / network down)
        hardError = true
        setScanStatus({
          running: false,
          finished: true,
          message: msg || 'שגיאה בהתחלת סריקה',
          total_found: 0,
          total_matches: 0,
          log: [{ time: '', level: 'error', message: msg || 'שגיאה' }],
        })
        setScanning(false)
      }
    }

    if (hardError) return

    // Start polling /scan/status every 2 seconds regardless of whether
    // startScan() succeeded or timed out.
    pollRef.current = setInterval(async () => {
      try {
        const status = await getScanStatus()
        setScanStatus(status)

        if (status.finished && !status.running) {
          if (pollRef.current) clearInterval(pollRef.current)
          pollRef.current = null
          setScanning(false)
          setToast(`הסריקה הושלמה — ${status.total_matches} התאמות חדשות`)
          load('latest')
          setViewMode('latest')
        }
      } catch {
        // Transient network hiccup — keep polling
      }
    }, 2000)
  }

  async function handleWeeklyReport() {
    setWeeklyReportToast('')
    setWeeklyReportLoading(true)
    try {
      const res = await requestWeeklyReport()
      setWeeklyReportToast(
        res.ok
          ? res.properties_count > 0
            ? `הדוח השבועי נשלח למייל (${res.properties_count} דירות)`
            : 'הדוח השבועי נשלח למייל'
          : res.message || 'שגיאה בהפקת הדוח'
      )
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
    <div className="space-y-5">
      {/* Agent summary card */}
      <div className="bg-gradient-to-l from-teal-50 to-white rounded-2xl border-2 border-teal-100 shadow-sm p-4 sm:p-6 flex gap-4 items-start">
        <div className="hidden sm:flex shrink-0 w-12 h-12 rounded-2xl bg-teal-100 text-teal-600 items-center justify-center">
          <AgentIcon className="w-7 h-7" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-base sm:text-xl font-bold text-slate-800 mb-1">הסוכן של {user.name}</h2>
          <p className="text-slate-600 text-xs sm:text-sm mb-4 leading-relaxed">
            סורק {user.target_cities?.length || 0} ערים · שולח התראות ל‑{user.email}
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-2 rounded-xl bg-white border border-slate-200 shadow-sm text-xs font-medium">
              <span className="font-semibold text-slate-800">{user.target_cities?.length || 0}</span>
              <span className="text-slate-600 mr-1">ערים</span>
            </span>
            <span className="px-3 py-2 rounded-xl bg-white border border-slate-200 shadow-sm text-xs font-medium">
              <span className="font-semibold text-slate-800">{maxRepay.toLocaleString()}₪</span>
              <span className="text-slate-600 mr-1">החזר מקסימלי</span>
            </span>
            <span className="px-3 py-2 rounded-xl bg-white border border-slate-200 shadow-sm text-xs font-medium">
              <span className="font-semibold text-slate-800">{user.equity?.toLocaleString()}₪</span>
              <span className="text-slate-600 mr-1">הון עצמי</span>
            </span>
            <span className="px-3 py-2 rounded-xl bg-white border border-slate-200 shadow-sm text-xs font-medium text-slate-700">
              {searchLabel}
            </span>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleRunScan}
          disabled={scanning}
          className="flex-1 sm:flex-none px-4 sm:px-5 py-3 rounded-xl font-semibold text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-colors text-sm"
        >
          {scanning ? 'הסוכן עובד...' : 'שלח את הסוכן לסרוק'}
        </button>
        <button
          type="button"
          onClick={handleWeeklyReport}
          disabled={weeklyReportLoading}
          className="flex-1 sm:flex-none px-4 sm:px-5 py-3 rounded-xl font-semibold border-2 border-teal-500 text-teal-700 hover:bg-teal-50 disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-colors text-sm"
        >
          {weeklyReportLoading ? 'מפיק דוח...' : 'דוח שבועי'}
        </button>
      </div>

      {weeklyReportToast && <p className="text-teal-600 font-medium text-sm">{weeklyReportToast}</p>}
      <p className="text-xs text-slate-500">דוח שבועי נשלח אוטומטית גם כל חמישי ב‑21:00 למייל שלך.</p>

      {/* Live scan console — shown as soon as scanning starts */}
      {(scanning || scanStatus) && (
        <div className="bg-slate-900 rounded-2xl border border-slate-700 shadow-lg overflow-hidden">
          {/* Console header */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-slate-800 border-b border-slate-700">
            <div className="flex items-center gap-2">
              {scanning && (
                <span className="inline-block w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
              )}
              <span className="text-xs font-semibold text-slate-200">
                {scanning ? 'הסוכן עובד' : 'סיכום סריקה'}
              </span>
            </div>
            {scanStatus && !scanning && (
              <button
                type="button"
                onClick={() => setShowLog(!showLog)}
                className="text-xs text-slate-400 hover:text-slate-200 transition-colors focus:outline-none"
              >
                {showLog ? 'הסתר לוג' : 'הצג לוג מלא'}
              </button>
            )}
          </div>

          {/* Current status line */}
          <div className="px-4 py-3">
            <p className="text-sm font-mono text-teal-300 leading-relaxed">
              {scanStatus?.message ?? 'מתחיל סריקה...'}
            </p>
            {scanStatus?.finished && !scanning && (
              <p className="mt-1 text-xs text-slate-400 font-mono">
                נסרקו {scanStatus.total_found} דירות · נשמרו {scanStatus.total_matches} התאמות
              </p>
            )}
          </div>

          {/* Rejection breakdown — shown only after scan finishes */}
          {scanStatus?.finished && !scanning && (
            <RejectionBreakdown
              total={scanStatus.total_found}
              rejections={scanStatus.rejections ?? {}}
            />
          )}

          {/* Scrollable log — toggled by "הצג לוג מלא" */}
          {showLog && scanStatus && scanStatus.log.length > 0 && (
            <div
              ref={logBoxRef}
              className="px-4 pb-4 max-h-56 overflow-y-auto font-mono text-xs space-y-0.5 border-t border-slate-700 pt-3"
            >
              {scanStatus.log.map((line, idx) => (
                <div key={idx} className={LOG_LEVEL_CLASS[line.level] ?? 'text-slate-300'}>
                  {line.time && <span className="text-slate-500 mr-2">{line.time}</span>}
                  {line.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {toast && <p className="text-teal-600 font-medium text-sm">{toast}</p>}

      {/* View toggle: Latest Scan / All Properties */}
      <div className="flex items-center gap-3 pb-4 border-b border-slate-200">
        <div className="inline-flex rounded-xl bg-slate-100 p-1 gap-1">
          <button
            type="button"
            onClick={() => setViewMode('latest')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
              viewMode === 'latest' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            סריקה אחרונה
          </button>
          <button
            type="button"
            onClick={() => setViewMode('all')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
              viewMode === 'all' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            כל הדירות שנמצאו
          </button>
        </div>
        <span className="px-3 py-1.5 rounded-xl bg-teal-600 text-white text-xs font-semibold">
          {filteredByCity.length}
        </span>
      </div>

      {/* Filters — shown only when there are properties */}
      {properties.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-3">
          <div>
            <span className="block text-xs font-semibold text-slate-500 mb-2">סוג עסקה</span>
            <div className="flex flex-wrap gap-2 overflow-x-auto pb-1">
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
            <div className="flex flex-wrap gap-2 overflow-x-auto pb-1">
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

      {/* Property list */}
      {loading ? (
        <p className="text-slate-500 text-sm py-6 text-center">טוען...</p>
      ) : filteredByCity.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
          <h3 className="text-base font-semibold text-slate-800 mb-2">
            {viewMode === 'latest' ? 'לא נמצאו דירות בסריקה האחרונה' : 'הסוכן ממתין לפקודה'}
          </h3>
          <p className="text-slate-500 text-sm">
            {viewMode === 'latest'
              ? 'לחץ על "שלח את הסוכן לסרוק" כדי להפעיל סריקה חדשה'
              : 'לחץ על "שלח את הסוכן לסרוק" כדי שיחפש עבורך דירות'}
          </p>
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
    </div>
  )
}
