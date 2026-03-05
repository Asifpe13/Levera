import { useState } from 'react'
import type { Property } from '../api'
import { PlaceholderHouse } from './illustrations'
import { ScoreRing, VerdictBanner, Badge } from './ui'

export default function PropertyCard({ prop }: { prop: Property }) {
  const [open, setOpen] = useState((prop.ai_score ?? 0) >= 70)
  const score = prop.ai_score ?? 0
  const deal = prop.deal_type === 'rent' ? 'שכירות' : 'מכירה'
  const city = prop.city || '?'
  const neighborhood = prop.neighborhood || ''
  const location = neighborhood ? `${city}, ${neighborhood}` : city
  const rooms = prop.rooms ?? '?'
  const price = prop.price ?? 0
  const listingUrl = (prop.listing_url || '').trim()
  const imageUrl = (prop.image_url || '').trim()
  const srcName = ['Yad2', 'Madlan', 'Homeless', 'WinWin'].includes(prop.source) ? prop.source : '?'

  return (
    <article className="bg-white rounded-2xl border-2 border-slate-200 overflow-hidden shadow-lg shadow-slate-200/50 hover:shadow-xl hover:border-teal-200 transition-all">
      {/* Header row - always visible */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full px-6 py-5 flex items-center justify-between gap-4 text-right bg-gradient-to-l from-slate-50 to-white hover:from-slate-100 hover:to-slate-50 transition-colors border-b border-slate-100"
      >
        <div className="flex flex-col items-start gap-1">
          <span className="text-base font-semibold text-slate-800">
            {location} · {rooms} חד׳ · {price.toLocaleString()} ₪ · {deal}
          </span>
          <div className="flex flex-wrap gap-2 items-center text-xs text-slate-500">
            <span>ציון התאמה לפי Levera</span>
            {prop.market_confidence != null && prop.deal_type === 'sale' && (
              <Badge variant={prop.market_confidence >= 60 ? 'success' : prop.market_confidence >= 40 ? 'warning' : 'neutral'}>
                ביטחון שוק {prop.market_confidence}%
              </Badge>
            )}
            {prop.value_label && (
              <Badge variant="accent">
                {prop.value_label}
              </Badge>
            )}
          </div>
        </div>
        <span className="flex items-center gap-3 shrink-0">
          <ScoreRing score={score} label="ציון" />
          <span className="text-xl text-slate-400">{open ? '▼' : '◀'}</span>
        </span>
      </button>

      {open && (
        <div className="flex flex-col md:flex-row bg-white">
          {/* Image or placeholder - large, left side in RTL (so first in DOM) */}
          <div className="md:w-[42%] shrink-0 bg-slate-100">
            <div className="aspect-[4/3] overflow-hidden">
              {imageUrl ? (
                listingUrl ? (
                  <a href={listingUrl} target="_blank" rel="noopener noreferrer" className="block h-full">
                    <img src={imageUrl} alt="דירה" className="w-full h-full object-cover hover:scale-105 transition-transform duration-300" />
                  </a>
                ) : (
                  <img src={imageUrl} alt="דירה" className="w-full h-full object-cover" />
                )
              ) : (
                <PlaceholderHouse />
              )}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 md:p-8 border-r-4 border-teal-500 min-w-0">
            <div className="flex flex-wrap gap-2 mb-4 items-center">
              <Badge variant="neutral">{srcName}</Badge>
              <Badge variant={prop.deal_type === 'rent' ? 'success' : 'primary'}>{deal}</Badge>
              {prop.price_drop && <Badge variant="warning">הורדת מחיר</Badge>}
            </div>

            <div className="mb-4">
              <VerdictBanner
                verdict={score >= 80 ? 'BUY' : score >= 60 ? 'INVEST' : score >= 40 ? 'CONSIDER' : 'REJECT'}
                confidence={score}
              />
            </div>

            {listingUrl && (
              <a
                href={listingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl font-bold text-white bg-teal-600 hover:bg-teal-700 shadow-lg shadow-teal-900/25 transition-all mb-6"
              >
                צפה במודעה המלאה — תמונות, טלפון ויצירת קשר
              </a>
            )}

            <div className="space-y-3 text-slate-700">
              {prop.address && (
                <p className="text-base"><strong className="text-slate-900">כתובת:</strong> {prop.address}</p>
              )}
              <p className="text-base">
                {prop.rooms != null && `חדרים: ${prop.rooms}`}
                {prop.floor != null && ` · קומה: ${prop.floor}`}
                {prop.size_sqm != null && ` · שטח: ${prop.size_sqm} מ"ר`}
              </p>
              {prop.deal_type === 'sale' && (prop.monthly_repayment != null || prop.loan_amount != null) && (
                <div className="mt-3 p-3 rounded-xl bg-amber-50 border border-amber-100 text-base">
                  <strong className="text-slate-900">משכנתא לפי חוק המשכנתא בישראל (בית ראשון):</strong>
                  <p className="text-slate-700 mt-1">
                    בית ראשון דורש 25% הון עצמי. בנקים לא מאשרים החזר מעל האחוז שהגדרת מההכנסה.
                  </p>
                  {prop.loan_amount != null && prop.loan_amount > 0 && (
                    <p className="text-slate-800 font-medium mt-1">סכום משכנתא צפוי: {prop.loan_amount.toLocaleString()} ₪</p>
                  )}
                  {prop.monthly_repayment != null && (
                    <p className="text-slate-800 font-medium">החזר חודשי משוער: {prop.monthly_repayment.toLocaleString()} ₪</p>
                  )}
                </div>
              )}
              {prop.deal_type === 'rent' && prop.monthly_repayment != null && (
                <p className="text-base"><strong className="text-slate-900">החזר חודשי משוער:</strong> {prop.monthly_repayment.toLocaleString()} ₪</p>
              )}
            </div>

            {prop.profile_area_message && (
              <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-700 leading-relaxed">
                {prop.profile_area_message}
              </div>
            )}

            {prop.ai_summary && (
              <div className="mt-5 p-4 rounded-xl bg-teal-50 border border-teal-100 text-slate-700 text-base leading-relaxed">
                {prop.ai_summary}
              </div>
            )}
            {(prop.market_summary_text || (prop.market_avg_per_sqm != null)) && (
              <div className="mt-4 p-3 rounded-xl bg-indigo-50 border border-indigo-100">
                <strong className="text-slate-800">השוואה לשוק (נתוני מדינה):</strong>
                <p className="text-slate-700 mr-2 mt-1">
                  {prop.market_summary_text ?? `דירות דומות באזור נמכרו בממוצע ב־₪${(prop.market_avg_per_sqm ?? 0).toLocaleString()} למ"ר לפי נתוני רכוש המסים.`}
                </p>
              </div>
            )}
            {prop.neighborhood_insights && (
              <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <strong className="text-slate-800">תובנות שכונה (AI):</strong>
                <span className="text-slate-700 mr-2"> {prop.neighborhood_insights}</span>
              </div>
            )}

            {listingUrl && (
              <a
                href={listingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 mt-6 px-4 py-2.5 rounded-xl font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
              >
                צפה במודעה המלאה ↗
              </a>
            )}
          </div>
        </div>
      )}
    </article>
  )
}
