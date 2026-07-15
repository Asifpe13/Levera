# Levera — Real Estate Decision Intelligence

סוכן נדל״ן חכם שמסנן אתרי מודעות, מחשב משכנתא ותזרים לפי החוק בישראל, משווה מחירים לנתוני מדינה ומציג רק דירות שעוברות את הקריטריונים הפיננסיים של המשתמש.

## מבנה הפרויקט

```
Levera/
├── backend/      ← שרת (FastAPI, DB, סורקים, AI, אימייל)
├── frontend/     ← לקוח (React + TypeScript + PWA + Capacitor)
└── .env          ← משתני סביבה (MONGODB_URI וכו')
```

## הרצה

### 1. Backend (API)

```bash
cd backend
pip install -r requirements.txt
python run_api.py
```

ה-API יעלה על http://127.0.0.1:8000  
בדיקה: http://127.0.0.1:8000/health

### 2. Frontend (React)

בטרמינל נפרד:

```bash
cd frontend
npm install
npm run dev
```

האפליקציה: http://localhost:5173 (משתמשת ב-API דרך proxy ל־8000).

### 3. סוכן ברקע (אופציונלי)

סריקה אוטומטית ודו"חות שבועיים:

```bash
cd backend
python main.py
```

---

קובץ `.env` יכול להימצא בשורש הפרויקט או בתיקיית `backend/` (לפחות `MONGODB_URI`).

---

## הרצה מקומית מלאה (בלי Render/Vercel)

**חשוב:** מריצים על המחשב **שלך** (לא בטרמינל של Cloud Agent) — הטלפון צריך להגיע למחשב באותה רשת Wi‑Fi.

### הגדרה לטלפון — כל מערכת הפעלה (Windows/macOS/Linux)

```bash
node scripts/setup-phone-dev.mjs
```

הסקריפט מזהה את ה-IP של המחשב ברשת וכותב את `mobile/.env` ו-`frontend/.env.local` אוטומטית.
אם זיהה IP שגוי (VPN/WSL): `node scripts/setup-phone-dev.mjs 192.168.x.x`

העתק `.env.example` ל-`.env` בשורש (נעשה אוטומטית ע"י הסקריפט). MongoDB מקומי דרך `docker compose up -d`, או Atlas ב-`MONGODB_URI`.

| רכיב | פקודה | כתובת |
|------|--------|--------|
| Backend | `cd backend && python run_api.py` | http://127.0.0.1:8000 |
| Web + PWA | `cd frontend && npm run dev` | http://localhost:5173 |
| React Native | `cd mobile && npm start` | Expo Go / emulator |

---

## אפליקציית מובייל

### 1. PWA — התקנה מהדפדפן
### 2. Capacitor — native shell
### 3. React Native (Expo) — `/mobile`

תכונות חדשות:
- **Push notifications** — device tokens + Expo/FCM (אופציונלי מקומית)
- **Offline mode** — IndexedDB (web) / AsyncStorage (Expo)
- **התראות בשרת** — `GET /notifications` (לא mock)
- **מפה + מצלמה** — באפליקציית Expo

ראה `mobile/README.md` לפרטים.
