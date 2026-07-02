# Levera — React Native (Expo)

אפליקציה native שמתחברת ל-backend **מקומי** — בלי Render/Vercel.

## דרישות

- Node 18+
- Backend רץ על `http://localhost:8000` (ראה `scripts/dev-local.sh` בשורש)
- Expo Go על הטלפון, או emulator

## הרצה

```bash
# מהשורש — backend + frontend web + הוראות mobile
./scripts/dev-local.sh

# או ידנית:
cd mobile
npm install
npm start
```

סרוק את ה-QR עם Expo Go.

## כתובת API

| סביבה | כתובת |
|--------|--------|
| iOS Simulator | `http://localhost:8000` |
| Android Emulator | `http://10.0.2.2:8000` |
| מכשיר físי + Expo | IP המחשב שלך, למשל `http://192.168.1.10:8000` |

הגדר ב-`.env`:

```
EXPO_PUBLIC_API_URL=http://192.168.1.10:8000
```

## תכונות

- **דירות** — רשימה + offline cache (AsyncStorage)
- **התראות** — מהשרת + Expo Push (כש-`EXPO_ACCESS_TOKEN` מוגדר ב-backend)
- **מפה** — react-native-maps + מיקום המשתמש
- **מצלמה** — expo-camera לצילום בשטח
- **הגדרות** — push toggle, התנתקות
