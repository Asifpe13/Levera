import { Link, useNavigate } from 'react-router-dom'
import { HeroRealEstate } from '../components/illustrations'
import { PROFILE_DEFINITIONS } from '../levereConfig'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-teal-50/40 to-slate-100 flex flex-col">
      <header className="w-full border-b border-slate-200/70 bg-white/80 backdrop-blur">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-600 text-white flex items-center justify-center font-black text-lg shadow-md shadow-teal-900/30">
              L
            </div>
            <div>
              <div className="font-semibold text-slate-800 text-base">Levera</div>
              <div className="text-[11px] text-slate-500">
                סוכן נדל״ן AI · קונה דירה / משקיע
              </div>
            </div>
          </div>
          <nav className="flex items-center gap-4 text-sm">
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="levera-btn levera-btn-secondary"
            >
              כניסה
            </button>
            <button
              type="button"
              onClick={() => navigate('/register')}
              className="levera-btn levera-btn-primary"
            >
              הפעל את הסוכן בחינם
            </button>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <section className="max-w-6xl mx-auto px-6 py-10 md:py-14 grid md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] gap-10 items-center">
          <div>
            <p className="text-xs font-semibold text-teal-700 tracking-wide mb-3">
              LEVERA · REAL ESTATE INTELLIGENCE
            </p>
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-extrabold text-slate-900 leading-tight mb-4">
              הסוכן החכם שמסנן
              <span className="text-teal-600"> את כל השטויות</span>
              <br />
              ומשאיר לך רק את הדירות הנכונות.
            </h1>
            <p className="text-slate-600 text-sm md:text-base leading-relaxed max-w-xl mb-6">
              Levera סורק עבורך אתרי נדל״ן, מנתח כל דירה לפי פרופיל פיננסי אישי (קונה
              בית ראשון, משקיע, תזרים מזומנים) ושולח לך רק התאמות שעוברות את כל
              הכללים של הבנקים והמשקיעים.
            </p>
            <div className="flex flex-wrap gap-3 mb-6">
              {['בדיקת משכנתא לפי חוק בישראל', 'השוואת מחיר לשוק (Gov Data)', 'התראות בזמן אמת למייל', 'דו״ח שבועי חכם'].map(
                (label) => (
                  <span
                    key={label}
                    className="levera-badge bg-teal-50 text-teal-800 border border-teal-100"
                  >
                    {label}
                  </span>
                ),
              )}
            </div>
            <div className="flex flex-wrap gap-3 items-center mb-3">
              <button
                type="button"
                onClick={() => navigate('/register')}
                className="levera-btn levera-btn-primary text-sm px-6 py-3"
              >
                התחל כסוכן אישי בחינם
              </button>
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="levera-btn levera-btn-secondary text-sm px-5 py-3"
              >
                כבר יש לי חשבון
              </button>
            </div>
            <p className="text-[11px] text-slate-500">
              אין צורך בכרטיס אשראי. החיבור למייל ולסוכן נעשה אחרי הרשמה.
            </p>
          </div>
          <div className="relative">
            <div className="absolute -inset-6 bg-gradient-to-b from-teal-100/60 via-transparent to-transparent rounded-[2rem] blur-2xl -z-10" />
            <div className="levera-card rounded-[2rem] p-6 md:p-7 h-full flex flex-col gap-4">
              <div className="flex items-center justify-between gap-3 mb-2">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-2xl bg-teal-600 text-white flex items-center justify-center font-bold text-lg">
                    AI
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-900">
                      סוכן Levera
                    </div>
                    <div className="text-[11px] text-slate-500">
                      פועל ברקע · סורק, מחשב, מסנן
                    </div>
                  </div>
                </div>
                <HeroRealEstate className="w-14 h-14 hidden sm:block" />
              </div>
              <div className="mt-1 mb-3">
                <p className="text-xs font-semibold text-slate-600 mb-2">
                  בחר את הפרופיל שמתאים לך:
                </p>
                <div className="grid gap-2">
                  {PROFILE_DEFINITIONS.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => navigate('/register')}
                      className="w-full text-right px-3.5 py-2.5 rounded-xl border border-slate-200 hover:border-teal-400 hover:bg-teal-50/60 text-xs transition-colors"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <div className="font-semibold text-slate-800 text-sm">
                            {p.label}
                          </div>
                          <div className="text-[11px] text-slate-500">
                            {p.tagline}
                          </div>
                        </div>
                        <span className="levera-badge bg-slate-900 text-slate-100">
                          {p.shortLabel}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
              <div className="border-t border-slate-200 pt-3 mt-1">
                <p className="text-[11px] text-slate-500 mb-1">
                  דוגמה להתראה:
                </p>
                <div className="flex flex-col gap-1 text-[11px] text-slate-700">
                  <div className="flex items-center justify-between">
                    <span>נמצאה דירה מתאימה בפתח תקווה</span>
                    <span className="levera-badge bg-emerald-100 text-emerald-800">
                      ציון התאמה 86
                    </span>
                  </div>
                  <span className="text-slate-500">
                    4 חד׳ · 1,050,000 ₪ · החזר חודשי 4,200 ₪ (33% מההכנסה)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-t border-slate-200/80 bg-white/70">
          <div className="max-w-6xl mx-auto px-6 py-8 grid md:grid-cols-3 gap-6 text-sm">
            <div>
              <h3 className="levera-section-title text-base mb-2">איך זה עובד?</h3>
              <p className="text-slate-600 leading-relaxed">
                Levera מתחבר לפרופיל שלך, סורק אתרי נדל״ן, מחשב את המשכנתא לפי חוק
                המשכנתאות בישראל, משווה למחירי שוק אמיתיים ומציג רק דירות שעוברות את
                כל החסמים.
              </p>
            </div>
            <div>
              <h3 className="levera-section-title text-base mb-2">למי זה מתאים?</h3>
              <ul className="text-slate-600 space-y-1.5">
                <li>• זוגות / יחידים שקונים דירה ראשונה ורוצים שקט מהבנק.</li>
                <li>• משקיעים שמחפשים איזון בין תשואה ליציבות.</li>
                <li>• מי שרוצה למקסם תזרים מזומנים משכירות.</li>
              </ul>
            </div>
            <div>
              <h3 className="levera-section-title text-base mb-2">צעד ראשון</h3>
              <p className="text-slate-600 mb-3">
                פתח פרופיל תוך דקה, הגדר הון עצמי, הכנסה וערים מועדפות — והסוכן שלך
                יתחיל לעבוד במקומך.
              </p>
              <Link to="/register" className="levera-btn levera-btn-accent w-full text-center">
                צור פרופיל והפעל את Levera
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white/80">
        <div className="max-w-6xl mx-auto px-6 py-4 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
          <span>Levera · Real Estate Decision Intelligence © 2026</span>
          <span>בנוי עבור שוק הנדל״ן הישראלי · Asif Perets</span>
        </div>
      </footer>
    </div>
  )
}

