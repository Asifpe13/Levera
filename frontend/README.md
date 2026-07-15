# Frontend — Levera (Real Estate Decision Intelligence)

React + TypeScript (Vite), RTL, PWA, Capacitor — עיצוב אחיד לדסקטופ ומובייל.

## הרצה

```bash
npm install
npm run dev
```

נפתח ב־http://localhost:5173. ה-API מתבצע דרך proxy ל־http://127.0.0.1:8000 (הרץ את ה-backend מתוך `../backend`).

## משתני סביבה

- `VITE_API_URL` — כתובת ה-API (ברירת מחדל: `/api` proxy ל־8000). **חובה בפרודקשן ובמובייל:** `https://levera-backend.onrender.com`

## PWA (התקנה מהדפדפן)

```bash
npm run build
npm run preview
```

לאחר build, האפליקציה כוללת Service Worker ו-manifest. בפרודקשן, משתמשים יכולים להוסיף למסך הבית.

## Capacitor (אפליקציה native)

```bash
npm run build
npx cap add android    # פעם ראשונה
npx cap add ios        # פעם ראשונה (macOS)
npm run cap:sync       # סנכרון web build → native
npm run cap:android    # פתיחת Android Studio
npm run cap:ios        # פתיחת Xcode
```

## סקריפטים נוספים

| סקריפט | תיאור |
|--------|--------|
| `npm run icons` | יצירת אייקוני PWA מ-`public/icons/icon.svg` |
| `npm run cap:sync` | build + סנכרון Capacitor |
| `npm run mobile:android` | build + הרצה על Android |
| `npm run mobile:ios` | build + הרצה על iOS |
