#!/bin/bash
cd "$(dirname "$0")/backend"
mkdir -p data
echo "Starting FocusAI PRO MONITOR..."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
