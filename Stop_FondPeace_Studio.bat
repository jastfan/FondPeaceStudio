@echo off
title Stop FondPeace Studio
echo Stopping FondPeace Studio background processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
echo FondPeace Studio server stopped successfully.
timeout /t 2
