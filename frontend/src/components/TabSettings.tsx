import { useState, useEffect } from 'react'
import type { User } from '../api'
import { updateUser, getCities } from '../api'
import { useAuth } from '../AuthContext'

const SEARCH_OPTS = [
  { value: 'both', label: 'קנייה + שכירות' },
  { value: 'buy', label: 'מכירה בלבד' },
  { value: 'rent', label: 'שכירות בלבד' },
] as const

const inputClass =
  'w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500'
const labelClass = 'block text-sm font-semibold text-slate-600 mb-1.5'

export default function TabSettings({ user }: { user: User }) {
  const { setUser } = useAuth()
  const [cities, setCities] = useState<string[]>([])
  const [name, setName] = useState(user.name)
  const [targetCities, setTargetCities] = useState<string[]>(user.target_cities)
  const [citySearch, setCitySearch] = useState('')
  const [searchType, setSearchType] = useState(user.search_type)
  const [profileType, setProfileType] = useState(user.profile_type ?? 'HOME_BUYER')
  const [homeIndex, setHomeIndex] = useState(user.home_index ?? 1)
  const [loanTermYears, setLoanTermYears] = useState(user.loan_term_years ?? 30)
  const [equity, setEquity] = useState(user.equity)
  const [monthlyIncome, setMonthlyIncome] = useState(user.monthly_income)
  const [maxRepaymentRatio, setMaxRepaymentRatio] = useState(Math.round(user.max_repayment_ratio * 100))
  const [roomRange, setRoomRange] = useState<[number, number]>([user.room_range_min, user.room_range_max])
  const [maxPrice, setMaxPrice] = useState(user.max_price ?? 0)
  const [rentRoomRange, setRentRoomRange] = useState<[number, number]>([user.rent_room_range_min, user.rent_room_range_max])
  const [maxRent, setMaxRent] = useState(user.max_rent ?? 0)
  const [extraPreferences, setExtraPreferences] = useState(user.extra_preferences || '')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getCities().then((r) => setCities(r.cities || []))
  }, [])

  const filteredCities = cities.filter((c) => {
    const q = citySearch.trim()
    if (!q) return true
    return c.toLowerCase().includes(q.toLowerCase())
  })

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSaved(false)
    try {
      const updated = await updateUser({
        name,
        target_cities: targetCities,
        search_type: searchType,
        profile_type: profileType,
        home_index: homeIndex,
        loan_term_years: loanTermYears,
        equity,
        monthly_income: monthlyIncome,
        room_range_min: roomRange[0],
        room_range_max: roomRange[1],
        max_price: maxPrice > 0 ? maxPrice : null,
        max_repayment_ratio: maxRepaymentRatio / 100,
        rent_room_range_min: rentRoomRange[0],
        rent_room_range_max: rentRoomRange[1],
        max_rent: maxRent > 0 ? maxRent : null,
        extra_preferences: extraPreferences || null,
      })
      setUser(updated)
      setSaved(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'שגיאה בשמירה')
    }
  }

  return (
    <>
      <h2 className="text-lg font-semibold text-slate-800 mb-6">עדכון פרופיל והעדפות</h2>
      <form onSubmit={handleSave} className="space-y-5">
        <div>
          <label className={labelClass}>שם</label>
          <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <label className={labelClass}>ערים לחיפוש</label>
          {targetCities.length > 0 && (
            <div className="mb-3">
              <span className="text-xs font-semibold text-slate-500 block mb-2">ערים שנבחרו</span>
              <div className="flex flex-wrap gap-2">
                {targetCities.map((city) => (
                  <span
                    key={city}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-teal-50 text-teal-800 border border-teal-200 text-sm font-medium"
                  >
                    {city}
                    <button
                      type="button"
                      onClick={() => setTargetCities(targetCities.filter((c) => c !== city))}
                      className="rounded-full p-0.5 hover:bg-teal-200/80 text-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-400"
                      aria-label={`הסר ${city}`}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
          <input
            className={`${inputClass} mb-2`}
            placeholder="התחל להקליד שם עיר כדי לסנן…"
            value={citySearch}
            onChange={(e) => setCitySearch(e.target.value)}
          />
          <div className="max-h-64 overflow-y-auto rounded-xl border border-slate-200 bg-white p-1 space-y-1">
            {filteredCities.map((c) => {
              const selected = targetCities.includes(c)
              return (
                <button
                  key={c}
                  type="button"
                  onClick={() =>
                    setTargetCities((prev) =>
                      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
                    )
                  }
                  className={`w-full text-right px-3 py-2 rounded-lg text-sm ${
                    selected
                      ? 'bg-teal-100 text-teal-800 font-semibold'
                      : 'bg-white text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {c}
                </button>
              )
            })}
          </div>
        </div>
        <div>
          <label className={labelClass}>סוג חיפוש</label>
          <div className="inline-flex rounded-full bg-slate-100 p-1 gap-0.5">
            {SEARCH_OPTS.map((o) => (
              <button
                key={o.value}
                type="button"
                onClick={() => setSearchType(o.value)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  searchType === o.value ? 'bg-white text-teal-600 shadow-sm' : 'text-slate-600 hover:text-slate-800'
                }`}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className={labelClass}>פרופיל החלטה</label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
            <button
              type="button"
              onClick={() => setProfileType('HOME_BUYER')}
              className={`px-3 py-2 rounded-xl border text-right ${
                profileType === 'HOME_BUYER'
                  ? 'border-teal-500 bg-teal-50 text-teal-800'
                  : 'border-slate-200 bg-white text-slate-700'
              }`}
            >
              <div className="font-semibold">קונה דירה ראשונה</div>
              <div className="text-[11px] text-slate-500">מיקוד ביציבות והחזר חודשי</div>
            </button>
            <button
              type="button"
              onClick={() => setProfileType('INVESTOR')}
              className={`px-3 py-2 rounded-xl border text-right ${
                profileType === 'INVESTOR'
                  ? 'border-teal-500 bg-teal-50 text-teal-800'
                  : 'border-slate-200 bg-white text-slate-700'
              }`}
            >
              <div className="font-semibold">משקיע מאוזן</div>
              <div className="text-[11px] text-slate-500">תשואה + עליית ערך + נזילות</div>
            </button>
            <button
              type="button"
              onClick={() => setProfileType('CASH_FLOW_MAXIMIZER')}
              className={`px-3 py-2 rounded-xl border text-right ${
                profileType === 'CASH_FLOW_MAXIMIZER'
                  ? 'border-teal-500 bg-teal-50 text-teal-800'
                  : 'border-slate-200 bg-white text-slate-700'
              }`}
            >
              <div className="font-semibold">מקסום תזרים</div>
              <div className="text-[11px] text-slate-500">כמה כסף נשאר כל חודש</div>
            </button>
          </div>
        </div>
        <div>
          <label className={labelClass}>סוג נכס מבחינת הבנק</label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
            <button
              type="button"
              onClick={() => setHomeIndex(1)}
              className={`px-3 py-2 rounded-xl border text-right ${
                homeIndex === 1
                  ? 'border-teal-500 bg-teal-50 text-teal-800'
                  : 'border-slate-200 bg-white text-slate-700'
              }`}
            >
              <div className="font-semibold">דירה ראשונה</div>
              <div className="text-[11px] text-slate-500">עד 75% מימון (25% הון עצמי)</div>
            </button>
            <button
              type="button"
              onClick={() => setHomeIndex(2)}
              className={`px-3 py-2 rounded-xl border text-right ${
                homeIndex === 2
                  ? 'border-teal-500 bg-teal-50 text-teal-800'
                  : 'border-slate-200 bg-white text-slate-700'
              }`}
            >
              <div className="font-semibold">דירה שנייה</div>
              <div className="text-[11px] text-slate-500">בדרך־כלל עד 50% מימון</div>
            </button>
            <button
              type="button"
              onClick={() => setHomeIndex(3)}
              className={`px-3 py-2 rounded-xl border text-right ${
                homeIndex === 3
                  ? 'border-teal-500 bg-teal-50 text-teal-800'
                  : 'border-slate-200 bg-white text-slate-700'
              }`}
            >
              <div className="font-semibold">דירה שלישית+</div>
              <div className="text-[11px] text-slate-500">מיועדת כהשקעה / תזרים</div>
            </button>
          </div>
        </div>
        <hr className="border-t border-slate-200 my-6" />
        <h3 className="text-base font-semibold text-slate-800 mb-3">🏠 הגדרות מכירה</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>הון עצמי (₪)</label>
            <input type="number" className={inputClass} value={equity} onChange={(e) => setEquity(Number(e.target.value))} step={10000} />
          </div>
          <div>
            <label className={labelClass}>הכנסה חודשית (₪)</label>
            <input type="number" className={inputClass} value={monthlyIncome} onChange={(e) => setMonthlyIncome(Number(e.target.value))} step={500} />
          </div>
        </div>
        <div>
          <label className={labelClass}>אחוז החזר מקסימלי</label>
          <input type="number" className={inputClass} min={20} max={50} value={maxRepaymentRatio} onChange={(e) => setMaxRepaymentRatio(Number(e.target.value))} />
        </div>
        <div>
          <label className={labelClass}>משך משכנתא מועדף (שנים)</label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={10}
              max={35}
              step={5}
              value={loanTermYears}
              onChange={(e) => setLoanTermYears(Number(e.target.value))}
              className="w-full accent-teal-600"
            />
            <span className="text-xs text-slate-600 whitespace-nowrap">{loanTermYears} שנה</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">
            Levera תחשב את ההחזר החודשי לפי מספר השנים שבחרת.
          </p>
        </div>
        <div>
          <label className={labelClass}>חדרים (מכירה)</label>
          <div className="flex items-center gap-2">
            <input type="number" className={inputClass} min={1} max={8} value={roomRange[0]} onChange={(e) => setRoomRange([Number(e.target.value), roomRange[1]])} />
            <span className="text-slate-400">–</span>
            <input type="number" className={inputClass} min={1} max={8} value={roomRange[1]} onChange={(e) => setRoomRange([roomRange[0], Number(e.target.value)])} />
          </div>
        </div>
        <div>
          <label className={labelClass}>תקציב מקסימלי למכירה (₪)</label>
          <input type="number" className={inputClass} value={maxPrice || ''} onChange={(e) => setMaxPrice(Number(e.target.value) || 0)} step={50000} />
        </div>
        <hr className="border-t border-slate-200 my-6" />
        <h3 className="text-base font-semibold text-slate-800 mb-3">🔑 הגדרות שכירות</h3>
        <div>
          <label className={labelClass}>חדרים (שכירות)</label>
          <div className="flex items-center gap-2">
            <input type="number" className={inputClass} min={1} max={8} value={rentRoomRange[0]} onChange={(e) => setRentRoomRange([Number(e.target.value), rentRoomRange[1]])} />
            <span className="text-slate-400">–</span>
            <input type="number" className={inputClass} min={1} max={8} value={rentRoomRange[1]} onChange={(e) => setRentRoomRange([rentRoomRange[0], Number(e.target.value)])} />
          </div>
        </div>
        <div>
          <label className={labelClass}>תקציב שכירות חודשי (₪)</label>
          <input type="number" className={inputClass} value={maxRent || ''} onChange={(e) => setMaxRent(Number(e.target.value) || 0)} step={500} />
        </div>
        <hr className="border-t border-slate-200 my-6" />
        <div>
          <label className={labelClass}>דרישות נוספות (לכל סוג)</label>
          <textarea className={`${inputClass} resize-y`} value={extraPreferences} onChange={(e) => setExtraPreferences(e.target.value)} rows={3} />
        </div>
        {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
        {saved && <p className="text-teal-600 font-medium">ההגדרות עודכנו ✓</p>}
        <button
          type="submit"
          className="px-5 py-3 rounded-xl font-semibold text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-colors"
        >
          שמור שינויים
        </button>
      </form>
    </>
  )
}
