#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDS_FILE="$PROJECT_DIR/.pids"

echo "⏹ Spegnimento SparklingOrbit..."

if [ -f "$PIDS_FILE" ]; then
    PIDS=$(cat "$PIDS_FILE")
    for PID in $PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" && echo "  Processo $PID fermato"
        fi
    done
    rm "$PIDS_FILE"
fi

# Sicurezza: kill per porta
lsof -i :8000 -n -P 2>/dev/null | grep LISTEN | awk '{print $2}' | xargs kill 2>/dev/null || true
lsof -i :3000 -n -P 2>/dev/null | grep LISTEN | awk '{print $2}' | xargs kill 2>/dev/null || true

echo "✅ Tutto spento."
