@echo off
cd /d "%~dp0backend"
echo Starting FocusAI PRO MONITOR...
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
