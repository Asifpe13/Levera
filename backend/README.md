# Backend — Levera

שרת FastAPI, מסד נתונים, סורקים, שירותי AI ואימייל.

## התקנה והרצה

```bash
pip install -r requirements.txt
python run_api.py
```

פורט 8000. משתני סביבה נטענים מ־`../.env` או מ־`.env` בתיקייה זו.

## מבנה

| תיקייה / קובץ | תיאור |
|---------------|--------|
| `api/` | FastAPI — auth, user, properties, scan, market, config |
| `run_api.py` | הרצת ה-API |
| `database/` | MongoDB + מודלים |
| `engine.py` | מנוע סריקה והתאמה |
| `scrapers/` | Yad2, Madlan, Homeless, WinWin |
| `services/` | AI, אימייל, scheduler |
| `config.py` | הגדרות + ערים |
| `logic.py` | לוגיקת התאמה |
| `main.py` | סוכן ברקע (סריקה + דו"ח שבועי) |
| `templates/` | תבניות אימייל |
