@echo off
title US Stock Fund Flow Dashboard
echo ========================================================
echo   US Stock Fund Flow Dashboard (Money Flow Analysis)
echo   Starting server...
echo ========================================================
cd /d "%~dp0"
python app.py
pause
