#!/usr/bin/env bash
# Run Levera fully locally — no Render/Vercel deploy required.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Levera local dev ==="
echo ""

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found — ensure MongoDB is running at mongodb://localhost:27017"
else
  echo "Starting MongoDB (docker compose)..."
  docker compose up -d
fi

echo ""
echo "1) Backend API → http://127.0.0.1:8000"
echo "   cd backend && pip install -r requirements.txt && python run_api.py"
echo ""
echo "2) Web frontend → http://localhost:5173"
echo "   cd frontend && npm install && npm run dev"
echo ""
echo "3) React Native (Expo) → scan QR with Expo Go"
echo "   cd mobile && npm install && npm start"
echo "   Android emulator API: http://10.0.2.2:8000"
echo "   Physical device: set EXPO_PUBLIC_API_URL=http://YOUR_LAN_IP:8000"
echo ""
echo "Optional push (local): set EXPO_ACCESS_TOKEN in backend/.env for Expo push delivery"
