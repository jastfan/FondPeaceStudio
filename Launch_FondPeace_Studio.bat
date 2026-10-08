@echo off
title FondPeace Studio — Viral Reel Engine
cd /d "%~dp0"
echo ====================================================
echo   Launching FondPeace Studio App Window...
echo ====================================================
python launch_app.py
timeout /t 2 >nul
