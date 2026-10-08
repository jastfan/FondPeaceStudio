@echo off
title Create FondPeace Studio Desktop App
cd /d "%~dp0"
python create_desktop_shortcut.py
echo.
echo =========================================================
echo  FondPeace Studio App shortcut is now on your Desktop!
echo =========================================================
timeout /t 3
