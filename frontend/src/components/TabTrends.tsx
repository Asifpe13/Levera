import { useState, useEffect } from 'react'
import { getMarketTrends } from '../api'
import type { MarketTrends } from '../api'
import { EmptyCharts } from './illustrations'

export default function TabTrends() {
  const [data, setData] = useState<MarketTrends | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getMarketTrends()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : 'שגיאה'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-slate-500">טוען...</p>
  if (error) return <p className="text-red-600">{error}</p>
  if (!data || data.total_ads === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
        <div className="flex justify-center mb-4">
          <EmptyCharts className="w-24 h-24" />
        </div>
        <h3 className="text-lg font-semibold text-slate-800 mb-2">אין עדיין נתונים</h3>
        <p className="text-slate-600">הרץ סריקה ולאחר שיישמרו דירות יופיעו כאן מדדים וגרפים.</p>
      </div>
    )
  }

  const hasCities = data.cities && data.cities.length > 0

  return (
    <>
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-1">מגמות שוק</h3>
        <p className="text-slate-600 text-sm">
          סקירה לפי עיר — ממוצע מחיר ומספר המודעות מהדירות שהסוכן שמר. מכירה ושכירות מוצגים בנפרד.
        </p>
      </div>

      {/* הערים שנבחרו – מוצגות בראש */}
      {hasCities && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-slate-600 mb-2">ערים במגמה</h4>
          <div className="flex flex-wrap gap-2">
            {data.cities.map((city) => (
              <span
                key={city}
                className="inline-flex items-center px-4 py-2 rounded-xl bg-teal-50 text-teal-800 border border-teal-200 text-sm font-medium"
              >
                {city}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-4 mb-6">
        <div className="min-w-[140px] bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="text-2xl font-bold text-slate-800">{data.total_ads}</div>
          <div className="text-sm text-slate-500">סה&quot;כ מודעות</div>
        </div>
        <div className="min-w-[140px] bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="text-2xl font-bold text-slate-800">{data.n_cities}</div>
          <div className="text-sm text-slate-500">ערים</div>
        </div>
        <div className="min-w-[140px] bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="text-2xl font-bold text-slate-800">{data.avg_sale > 0 ? data.avg_sale.toLocaleString() + ' ₪' : '—'}</div>
          <div className="text-sm text-slate-500">ממוצע מחיר מכירה</div>
        </div>
        <div className="min-w-[140px] bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="text-2xl font-bold text-slate-800">{data.avg_rent > 0 ? data.avg_rent.toLocaleString() + ' ₪' : '—'}</div>
          <div className="text-sm text-slate-500">ממוצע מחיר שכירות</div>
        </div>
      </div>

      {/* ממוצע מחיר לפי עיר – מכירה */}
      {data.by_city_sale.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-4 shadow-sm">
          <h4 className="text-base font-semibold text-slate-800 mb-4">ממוצע מחיר לפי עיר — מכירה</h4>
          <div className="space-y-2">
            {data.by_city_sale.map((row) => (
              <div key={row.city} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
                <span className="text-slate-700">{row.city}</span>
                <span className="font-semibold text-slate-800">{row.avg_price.toLocaleString()} ₪</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ממוצע מחיר לפי עיר – שכירות */}
      {data.by_city_rent.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-4 shadow-sm">
          <h4 className="text-base font-semibold text-slate-800 mb-4">ממוצע מחיר לפי עיר — שכירות</h4>
          <div className="space-y-2">
            {data.by_city_rent.map((row) => (
              <div key={row.city} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
                <span className="text-slate-700">{row.city}</span>
                <span className="font-semibold text-slate-800">{row.avg_price.toLocaleString()} ₪</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* מספר מודעות לפי עיר – מכירה */}
      {data.by_city_sale.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-4 shadow-sm">
          <h4 className="text-base font-semibold text-slate-800 mb-4">מספר מודעות לפי עיר — מכירה</h4>
          <div className="space-y-2">
            {data.by_city_sale.map((row) => (
              <div key={row.city} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
                <span className="text-slate-700">{row.city}</span>
                <span className="font-semibold text-slate-800">{row.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* מספר מודעות לפי עיר – שכירות */}
      {data.by_city_rent.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <h4 className="text-base font-semibold text-slate-800 mb-4">מספר מודעות לפי עיר — שכירות</h4>
          <div className="space-y-2">
            {data.by_city_rent.map((row) => (
              <div key={row.city} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
                <span className="text-slate-700">{row.city}</span>
                <span className="font-semibold text-slate-800">{row.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
