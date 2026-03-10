import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { register, getCities } from '../api'
import { HeroRealEstate } from '../components/illustrations'

const SEARCH_TYPE_LABELS: Record<string, string> = {
  both: 'קנייה + שכירות',
  buy: 'קנייה',
  rent: 'שכירות',
}

const inputClass =
  'levera-input'
const labelClass = 'levera-label'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { setToken } = useAuth()
  const [cities, setCities] = useState<string[]>([])
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [equity, setEquity] = useState(400_000)
  const [monthlyIncome, setMonthlyIncome] = useState(12_500)
  const [maxRepaymentRatio, setMaxRepaymentRatio] = useState(40)
  const [targetCities, setTargetCities] = useState<string[]>([])
  const [searchType, setSearchType] = useState<'both' | 'buy' | 'rent'>('both')
  const [profileType, setProfileType] = useState<'HOME_BUYER' | 'INVESTOR' | 'CASH_FLOW_MAXIMIZER'>('HOME_BUYER')
  const [homeIndex, setHomeIndex] = useState<1 | 2 | 3>(1)
  const [loanTermYears, setLoanTermYears] = useState(30)
  const [roomRange, setRoomRange] = useState<[number, number]>([3, 5])
  const [maxPrice, setMaxPrice] = useState(0)
  const [rentRoomRange, setRentRoomRange] = useState<[number, number]>([2, 5])
  const [maxRent, setMaxRent] = useState(0)
  const [extraPreferences, setExtraPreferences] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    getCities().then((r) => setCities(r.cities || []))
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!name.trim() || !email.trim()) {
      setError('יש להזין שם ואימייל')
      return
    }
    if (targetCities.length === 0) {
      setError('יש לבחור לפחות עיר אחת')
      return
    }
    try {
      const res = await register({
        name: name.trim(),
        email: email.trim(),
        equity,
        monthly_income: monthlyIncome,
        max_repayment_ratio: maxRepaymentRatio / 100,
        target_cities: targetCities,
        search_type: searchType,
        room_range_min: roomRange[0],
        room_range_max: roomRange[1],
        max_price: maxPrice > 0 ? maxPrice : null,
        rent_room_range_min: rentRoomRange[0],
        rent_room_range_max: rentRoomRange[1],
        max_rent: maxRent > 0 ? maxRent : null,
        extra_preferences: extraPreferences || null,
        profile_type: profileType,
        home_index: homeIndex,
        loan_term_years: loanTermYears,
      })
      if (res.token) {
        setToken(res.token)
        navigate('/app', { replace: true })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'שגיאה בהרשמה')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-50 flex items-center justify-center px-4 py-10 sm:py-8">
      <button
        type="button"
        onClick={() => navigate('/')}
        className="absolute top-4 left-4 md:top-6 md:left-6 text-xs md:text-sm text-slate-100/80 hover:text-white bg-slate-900/50 border border-slate-700/70 rounded-full px-3 py-1 shadow-sm z-10"
      >
        ← חזרה לעמוד הראשי
      </button>
      <div className="w-full max-w-5xl mx-auto grid md:grid-cols-[minmax(0,1.2fr)_minmax(0,1.1fr)] gap-6 md:gap-8 items-stretch mt-8 md:mt-0">
        {/* Brand column */}
        <div className="hidden md:flex flex-col justify-between rounded-3xl bg-gradient-to-b from-teal-500 via-teal-600 to-emerald-600 p-7 shadow-[0_24px_80px_rgba(15,23,42,0.7)] border border-teal-300/40">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-11 h-11 rounded-2xl bg-slate-950/10 backdrop-blur text-white flex items-center justify-center font-black text-lg">
                L
              </div>
              <div>
                <div className="text-sm font-semibold uppercase tracking-[0.14em] text-teal-50">
                  LEVERA
                </div>
                <div className="text-[11px] text-teal-100">
                  Real Estate Decision Intelligence
                </div>
              </div>
            </div>
            <h1 className="text-3xl font-extrabold leading-snug mb-3 text-white">
              הגדר את הפרופיל הפיננסי שלך
              <br />
              ו‑Levera תעבוד במקומך.
            </h1>
            <p className="text-sm text-teal-50/90 leading-relaxed mb-6 max-w-md">
              כמה הון עצמי יש לך, מה גובה ההכנסה, באילו ערים לחפש ואיזה סוג עסקאות מעניינות אותך —
              מזה Levera בונה פרופיל החלטה: קונה דירה ראשונה, משקיע מאוזן או מקסימום תזרים.
            </p>
            <div className="flex flex-wrap gap-2 text-[11px]">
              {['בדיקת משכנתא לפי חוק בישראל', 'התאמת עסקאות לפרופיל אישי', 'התראות רק על דירות שעוברות סף', 'דו״חות שבועיים למייל'].map(
                (label) => (
                  <span
                    key={label}
                    className="inline-flex items-center px-3 py-1.5 rounded-full bg-slate-950/15 text-teal-50 border border-teal-100/40 font-medium"
                  >
                    {label}
                  </span>
                ),
              )}
            </div>
          </div>
          <div className="mt-8 flex items-center justify-between gap-4 text-[11px] text-teal-50/80">
            <div>
              <div className="font-semibold">למה צריך פרופיל?</div>
              <p className="mt-1 leading-relaxed">
                הפרופיל קובע האם Levera תפסול דירה בגלל החזר חודשי גבוה מדי, הון עצמי חסר או
                תזרים מזומנים שלילי. כך אתה רואה רק עסקאות שבאמת אפשריות עבורך.
              </p>
            </div>
            <HeroRealEstate className="w-20 h-20 opacity-90 hidden lg:block" />
          </div>
        </div>

        {/* Form card */}
        <div className="levera-card rounded-2xl sm:rounded-3xl p-5 sm:p-7 md:p-8 bg-white/95 backdrop-blur border-slate-200/90 shadow-[0_18px_50px_rgba(15,23,42,0.22)] w-full">
          <h2 className="text-xl font-bold text-slate-900 mb-1">יצירת חשבון חדש</h2>
          <p className="text-xs text-slate-500 mb-6">
            זה לוקח פחות מדקה. הנתונים ישמשו רק לחישובי התאמה, לא לשיתוף חיצוני.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5 text-sm">
            <div>
              <div className={labelClass}>פרטים אישיים</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className={labelClass}>שם מלא</label>
                  <input
                    className={inputClass}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="ישראל ישראלי"
                  />
                </div>
                <div>
                  <label className={labelClass}>אימייל</label>
                  <input
                    type="email"
                    className={inputClass}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@email.com"
                  />
                </div>
              </div>
            </div>

            <div>
              <div className={labelClass}>מצב כלכלי</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className={labelClass}>הון עצמי (₪)</label>
                  <input
                    type="number"
                    className={inputClass}
                    value={equity}
                    onChange={(e) => setEquity(Number(e.target.value))}
                    step={10000}
                  />
                </div>
                <div>
                  <label className={labelClass}>הכנסה חודשית (₪)</label>
                  <input
                    type="number"
                    className={inputClass}
                    value={monthlyIncome}
                    onChange={(e) => setMonthlyIncome(Number(e.target.value))}
                    step={500}
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className={labelClass}>אחוז החזר מקסימלי (%)</label>
                <input
                  type="range"
                  min={20}
                  max={50}
                  step={5}
                  value={maxRepaymentRatio}
                  onChange={(e) => setMaxRepaymentRatio(Number(e.target.value))}
                  className="w-full accent-teal-600"
                />
                <span className="text-xs text-slate-600">{maxRepaymentRatio}%</span>
              </div>
              <div className="mt-4">
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
                  משכנתא ארוכה יותר מורידה החזר חודשי אך מגדילה סך הריבית לאורך השנים.
                </p>
              </div>
            </div>

            <div>
              <div className={labelClass}>העדפות חיפוש</div>
              <div className="inline-flex rounded-full bg-slate-100 p-1 gap-0.5 mb-3">
                {(['both', 'buy', 'rent'] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setSearchType(t)}
                    className={`px-4 py-2 rounded-full text-xs font-medium transition-colors ${
                      searchType === t ? 'bg-white text-teal-600 shadow-sm' : 'text-slate-600 hover:text-slate-800'
                    }`}
                  >
                    {SEARCH_TYPE_LABELS[t]}
                  </button>
                ))}
              </div>
              <div>
                <label className={labelClass}>ערים לחיפוש</label>
                <select
                  className={`${inputClass} min-h-[110px]`}
                  multiple
                  value={targetCities}
                  onChange={(e) =>
                    setTargetCities(Array.from(e.target.selectedOptions, (o) => o.value))
                  }
                >
                  {cities.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
                <small className="text-slate-500 text-[11px]">החזק Ctrl לבחירה מרובה</small>
              </div>
            </div>

            <div>
              <div className={labelClass}>פרופיל החלטה</div>
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>חדרים (מכירה)</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    className={inputClass}
                    min={1}
                    max={8}
                    value={roomRange[0]}
                    onChange={(e) => setRoomRange([Number(e.target.value), roomRange[1]])}
                  />
                  <span className="text-slate-400">–</span>
                  <input
                    type="number"
                    className={inputClass}
                    min={1}
                    max={8}
                    value={roomRange[1]}
                    onChange={(e) => setRoomRange([roomRange[0], Number(e.target.value)])}
                  />
                </div>
              </div>
              <div>
                <label className={labelClass}>תקציב מקסימלי למכירה (₪)</label>
                <input
                  type="number"
                  className={inputClass}
                  value={maxPrice || ''}
                  onChange={(e) => setMaxPrice(Number(e.target.value) || 0)}
                  step={50000}
                  placeholder="0 = ללא הגבלה"
                />
              </div>
            </div>

            <div>
              <div className={labelClass}>סוג נכס מבחינת הבנק</div>
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>חדרים (שכירות)</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    className={inputClass}
                    min={1}
                    max={8}
                    value={rentRoomRange[0]}
                    onChange={(e) => setRentRoomRange([Number(e.target.value), rentRoomRange[1]])}
                  />
                  <span className="text-slate-400">–</span>
                  <input
                    type="number"
                    className={inputClass}
                    min={1}
                    max={8}
                    value={rentRoomRange[1]}
                    onChange={(e) =>
                      setRentRoomRange([rentRoomRange[0], Number(e.target.value)])
                    }
                  />
                </div>
              </div>
              <div>
                <label className={labelClass}>תקציב שכירות חודשי (₪)</label>
                <input
                  type="number"
                  className={inputClass}
                  value={maxRent || ''}
                  onChange={(e) => setMaxRent(Number(e.target.value) || 0)}
                  step={500}
                  placeholder="0 = ללא הגבלה"
                />
              </div>
            </div>

            <div>
              <label className={labelClass}>דרישות נוספות</label>
              <textarea
                className={`${inputClass} resize-y`}
                value={extraPreferences}
                onChange={(e) => setExtraPreferences(e.target.value)}
                placeholder="ממ״ד, מעלית, קומה גבוהה..."
                rows={3}
              />
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg border border-red-100">
                {error}
              </p>
            )}

            <button
              type="submit"
              className="levera-btn levera-btn-primary w-full mt-1"
            >
              צור חשבון והפעל את הסוכן
            </button>
          </form>

          <div className="mt-6 border-t border-slate-200 pt-4 text-xs text-slate-500 flex flex-col gap-2">
            <p>
              כבר יש לך חשבון?{' '}
              <Link to="/login" className="text-teal-700 font-semibold hover:underline">
                כניסה
              </Link>
            </p>
            <p className="text-[11px] text-slate-400">
              Levera בודקת התאמה לפי חוקי המשכנתא בישראל, אבל לא מחליפה ייעוץ מקצועי.
            </p>
            <p className="mt-2 text-[11px] text-slate-400">Levera © 2026 · Asif Perets</p>
          </div>
        </div>
      </div>
    </div>
  )
}