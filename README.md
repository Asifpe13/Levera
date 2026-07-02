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

## אפליקציית מובייל

הפרונטאנד תומך בשלוש דרכים לשימוש מהטלפון:

### 1. PWA — התקנה מהדפדפן (הכי מהיר)

1. בנה והעלה לפרודקשן עם `VITE_API_URL=https://levera-backend.onrender.com`
2. מהטלפון, פתח את האתר ב-Chrome (Android) או Safari (iOS)
3. Android: תפריט → "הוסף למסך הבית" | iOS: שיתוף → "הוסף למסך הבית"
4. האפליקציה תיפתח במצב standalone עם ניווט תחתון מותאם למובייל

### 2. Capacitor — אפליקציה native (App Store / Play Store)

```bash
cd frontend
npm install
npm run build

# הוספת פלטפורמות (פעם ראשונה בלבד)
npx cap add android
npx cap add ios

# סנכרון ובנייה
npm run cap:sync
npm run cap:android   # פותח Android Studio
npm run cap:ios       # פותח Xcode (macOS בלבד)
```

**משתנה סביבה חובה לפרודקשן:** `VITE_API_URL=https://levera-backend.onrender.com`

### 3. תכונות מובייל

- **PWA** — Service Worker, manifest, התקנה למסך הבית
- **ניווט תחתון** — תפריט תחתון במובייל (דירות, פרופילים, התראות, שוק, הגדרות)
- **Safe areas** — תמיכה ב-notch וב-home indicator
- **Capacitor** — Status bar, splash screen, כפתור חזרה ב-Android
- **באנר התקנה** — הצעה להוסיף למסך הבית בדפדפן
