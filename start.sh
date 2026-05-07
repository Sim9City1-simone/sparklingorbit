#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "▶ Avvio SparklingOrbit..."

# Backend
cd "$BACKEND_DIR"
set -a && source .env && set +a
.venv/bin/python3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "  Backend avviato (PID $BACKEND_PID) → http://localhost:8000"

# Frontend
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
echo "  Frontend avviato (PID $FRONTEND_PID) → http://localhost:3000"

# Salva i PID per lo stop
echo "$BACKEND_PID $FRONTEND_PID" > "$PROJECT_DIR/.pids"

echo ""
echo "✅ Tutto pronto! Apri http://localhost:3000"
echo "   Per spegnere tutto: ./stop.sh"
