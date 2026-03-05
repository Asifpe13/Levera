# Levera — Real Estate Decision Intelligence

סוכן נדל״ן חכם שמסנן אתרי מודעות, מחשב משכנתא ותזרים לפי החוק בישראל, משווה מחירים לנתוני מדינה ומציג רק דירות שעוברות את הקריטריונים הפיננסיים של המשתמש.

## מבנה הפרויקט

```
Levera/
├── backend/      ← שרת (FastAPI, DB, סורקים, AI, אימייל)
├── frontend/     ← לקוח (React + TypeScript)
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
