import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { login } from '../api'
import { HeroRealEstate } from '../components/illustrations'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setToken } = useAuth()
  const [email, setEmail] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!email.trim()) {
      setError('יש להזין כתובת אימייל')
      return
    }
    try {
      const res = await login(email, rememberMe)
      if (res.token) {
        setToken(res.token)
        navigate('/app', { replace: true })
        return
      }
      setError('לא נמצא חשבון עם אימייל זה. עבור להרשמה חדשה כדי ליצור חשבון.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'שגיאה בהתחברות')
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
      <div className="w-full max-w-5xl mx-auto grid md:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] gap-6 md:gap-8 items-stretch mt-8 md:mt-0">
        {/* Brand / story column */}
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
              ברוך הבא לסוכן הנדל״ן
              <br />
              שחושב כמו אנליסט השקעות.
            </h1>
            <p className="text-sm text-teal-50/90 leading-relaxed mb-6 max-w-md">
              Levera סורקת עבורך את השוק, מחשבת משכנתא לפי חוק בישראל, משווה מחירי דירות
              לנתוני מדינה ומציפה רק עסקאות שעוברות את כל הקריטריונים הפיננסיים שלך.
            </p>
            <div className="flex flex-wrap gap-2 text-[11px]">
              {[
                'בדיקת משכנתא לפי חוק',
                'Market Confidence לפי Gov Data',
                'התראות בזמן אמת למייל',
                'דו״ח שבועי חכם',
              ].map((label) => (
                <span
                  key={label}
                  className="inline-flex items-center px-3 py-1.5 rounded-full bg-slate-950/15 text-teal-50 border border-teal-100/40 font-medium"
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
          <div className="mt-8 flex items-center justify-between gap-4 text-[11px] text-teal-50/80">
            <div>
              <div className="font-semibold">איך זה עובד?</div>
              <p className="mt-1 leading-relaxed">
                אתה מגדיר הון עצמי, הכנסה ויעדים. Levera מתאימה את עצמה לפרופיל שלך —
                קונה דירה ראשונה, משקיע מאוזן או מקסימום תזרים — ומדרגת כל דירה בהתאם.
              </p>
            </div>
            <HeroRealEstate className="w-20 h-20 opacity-90 hidden lg:block" />
          </div>
        </div>

        {/* Login card */}
        <div className="levera-card rounded-2xl sm:rounded-3xl p-5 sm:p-7 md:p-8 bg-white/95 backdrop-blur border-slate-200/90 shadow-[0_18px_50px_rgba(15,23,42,0.22)] w-full">
          <div className="mb-6 flex justify-between items-center gap-3">
            <div>
              <p className="text-[11px] font-semibold text-teal-600 mb-1 uppercase tracking-[0.16em]">
                LEVERA PORTAL
              </p>
              <h2 className="text-xl font-bold text-slate-900 mb-1">כניסה לחשבון האישי</h2>
              <p className="text-xs text-slate-500">
                התחבר כדי לראות את הדירות שנבחרו עבורך, התראות ודוחות חכמים.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label htmlFor="email" className="levera-label">
                כתובת אימייל
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                className="levera-input"
              />
            </div>
            <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-600">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
              />
              <span>הישאר מחובר (התנתקות אוטומטית אחרי שבוע לבטיחות).</span>
            </label>
            {rememberMe && (
              <p className="text-[11px] text-slate-500">
                טיפ: אחרי הכניסה, שמור את העמוד במועדפים לכניסה מהירה.
              </p>
            )}
            {error && (
              <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg border border-red-100">
                {error}
              </p>
            )}
            <button type="submit" className="levera-btn levera-btn-primary w-full mt-1">
              כניסה ל‑Levera
            </button>
          </form>

          <div className="mt-6 border-t border-slate-200 pt-4 text-xs text-slate-500 flex flex-col gap-2">
            <p>
              אין לך חשבון?{' '}
              <Link to="/register" className="text-teal-700 font-semibold hover:underline">
                יצירת חשבון חדש
              </Link>
            </p>
            <p className="text-[11px] text-slate-400">
              Levera לא מבצעת פעולות בשמך — רק מנתחת נתונים ומסייעת לך לקבל החלטות חכמות.
            </p>
            <p className="mt-2 text-[11px] text-slate-400">Levera © 2026 · Asif Perets</p>
          </div>
        </div>
      </div>
    </div>
  )
}