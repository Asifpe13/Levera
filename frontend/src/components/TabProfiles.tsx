import type { User } from '../api'
import type { ProfileDefinition, ProfileType } from '../levereConfig'
import { Badge } from './ui'

interface TabProfilesProps {
  user: User
  profiles: ProfileDefinition[]
  activeProfileId: ProfileType
  onChangeActiveProfile: (id: ProfileType) => void
}

export default function TabProfiles({
  user,
  profiles,
  activeProfileId,
  onChangeActiveProfile,
}: TabProfilesProps) {
  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-lg font-semibold text-slate-800 mb-1">ניהול פרופילי החלטה</h2>
        <p className="text-sm text-slate-600 max-w-2xl">
          Levera יכול לחשב ולנתח את אותן דירות לפי זוויות שונות: קונה דירה ראשונה,
          משקיע מאוזן או מקסימום תזרים מזומנים. בחר את הפרופיל המרכזי שלך ואיך תרצה
          שהסוכן יסמן לך הזדמנויות.
        </p>
      </header>

      <section className="grid md:grid-cols-3 gap-4">
        {profiles.map((p) => {
          const active = p.id === activeProfileId
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onChangeActiveProfile(p.id)}
              className={`levera-card p-4 text-right transition-all cursor-pointer ${
                active
                  ? 'border-teal-500 shadow-md shadow-teal-900/10 ring-2 ring-teal-500/20'
                  : 'hover:border-teal-300 hover:shadow-md'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <h3 className="text-sm font-semibold text-slate-900">{p.label}</h3>
                {active ? (
                  <Badge variant="primary">פעיל כעת</Badge>
                ) : (
                  <Badge variant="neutral">זמין</Badge>
                )}
              </div>
              <p className="text-xs text-slate-600 mb-3">{p.tagline}</p>
              <p className="text-[11px] text-slate-500 leading-relaxed mb-3">{p.description}</p>
              <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
                <div className="rounded-xl bg-slate-50 border border-slate-200 px-3 py-2">
                  <div className="font-semibold text-slate-800 mb-0.5">{p.primaryKpiLabel}</div>
                  <div className="text-[10px] text-slate-500">
                    הסוכן ידרג דירות לפי מדד זה כמדד מרכזי.
                  </div>
                </div>
                <div className="rounded-xl bg-slate-50 border border-slate-200 px-3 py-2">
                  <div className="font-semibold text-slate-800 mb-0.5">{p.secondaryKpiLabel}</div>
                  <div className="text-[10px] text-slate-500">
                    משמש כמדד שניוני לקבלת החלטה ותיוג סיכון.
                  </div>
                </div>
              </div>
            </button>
          )
        })}
      </section>

      <section className="levera-card p-4 text-sm text-slate-700 space-y-2">
        <h3 className="text-sm font-semibold text-slate-800 mb-1">חיבור לפרופיל הפיננסי שלך</h3>
        <p>
          לפי הנתונים שהגדרת (הון עצמי{' '}
          <span className="font-semibold">{user.equity.toLocaleString()} ₪</span>, הכנסה חודשית{' '}
          <span className="font-semibold">{user.monthly_income.toLocaleString()} ₪</span> ויחס החזר
          מקסימלי{' '}
          <span className="font-semibold">{Math.round(user.max_repayment_ratio * 100)}%</span>){' '}
          הסוכן מחשב האם כל עסקה עומדת בכללי הבנק לפני שהוא מסמן אותה כהזדמנות.
        </p>
        <p className="text-xs text-slate-500">
          בעתיד תוכל להגדיר סף ציון שונה לכל פרופיל, תרחישי ריבית שונים ותזרים מזומנים ברמות
          סיכון שונות. כרגע המיקוד הוא בהתאמת הדירות לפרופיל הראשי שבחרת.
        </p>
      </section>
    </div>
  )
}

