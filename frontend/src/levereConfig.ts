export type ProfileType = 'HOME_BUYER' | 'INVESTOR' | 'CASH_FLOW_MAXIMIZER'

export interface ProfileDefinition {
  id: ProfileType
  label: string
  shortLabel: string
  tagline: string
  description: string
  primaryKpiLabel: string
  secondaryKpiLabel: string
}

export interface NotificationItem {
  id: string
  title: string
  message: string
  createdAt: string
  type: 'match' | 'scan' | 'weekly' | 'system'
  read: boolean
}

export const PROFILE_DEFINITIONS: ProfileDefinition[] = [
  {
    id: 'HOME_BUYER',
    label: 'קונה דירה ראשונה',
    shortLabel: 'Home Buyer',
    tagline: 'בטחון כלכלי ומגורים נוחים למשפחה.',
    description:
      'הסוכן מתמקד ביציבות, החזר חודשי עד 30–35% מההכנסה, אזורי מגורים טובים למשפחות ובחינת סיכון שמרנית לאורך זמן.',
    primaryKpiLabel: 'אחוז החזר משכנתא',
    secondaryKpiLabel: 'ציון יציבות אזורית',
  },
  {
    id: 'INVESTOR',
    label: 'משקיע מאוזן',
    shortLabel: 'Investor',
    tagline: 'איזון בין תשואה, עליית ערך ונזילות.',
    description:
      'התמקדות ב‑ROI, תשואה נטו ואפשרות יציאה קלה. הסוכן מניח החזקת נכס לטווח בינוני–ארוך ובוחן רגישות לריבית.',
    primaryKpiLabel: 'תשואה נטו משוערת',
    secondaryKpiLabel: 'פוטנציאל עליית ערך',
  },
  {
    id: 'CASH_FLOW_MAXIMIZER',
    label: 'מקסום תזרים מזומנים',
    shortLabel: 'Cash Flow',
    tagline: 'מקסימום כסף פנוי בסוף חודש.',
    description:
      'התמקדות בתזרים חודשי חיובי, יחס שכר דירה/משכנתא ורמת סיכון בהכנסות. דירות עם תזרים שלילי נפסלות מוקדם.',
    primaryKpiLabel: 'תזרים חודשי משוער',
    secondaryKpiLabel: 'יחס שכר דירה / משכנתא',
  },
]

export const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'n1',
    title: 'נמצאה התאמה חדשה בפתח תקווה',
    message: 'דירת 4 חד׳ ברחוב העצמאות נכנסה לטופ 10% עבור פרופיל Home Buyer.',
    createdAt: new Date().toISOString(),
    type: 'match',
    read: false,
  },
  {
    id: 'n2',
    title: 'הסריקה האוטומטית הסתיימה',
    message: 'הסוכן סרק 84 מודעות חדשות ושמר 6 התאמות עבורך.',
    createdAt: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    type: 'scan',
    read: true,
  },
  {
    id: 'n3',
    title: 'הדוח השבועי נשלח למייל',
    message: 'סיכום מלא של העסקאות והדירות המובילות השבוע מחכה לך במייל.',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
    type: 'weekly',
    read: true,
  },
]

