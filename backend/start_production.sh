#!/bin/bash
set -e

# Start bgutil PO Token provider in background (listens on :4416)
# bgutil-ytdlp-pot-provider plugin auto-connects to http://127.0.0.1:4416
node /bgutil/server/build/main.js &

# Start FastAPI server (foreground — container exits if this dies)
exec uvicorn main:app --host 0.0.0.0 --port 8000
