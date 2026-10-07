@echo off
title FondPeace Studio — Viral Reel Engine
echo ===================================================
echo   Starting FondPeace Studio Web UI (Port 8000)...
echo ===================================================
cd /d "%~dp0"
start http://127.0.0.1:8000
python server.py
pause
