@echo off
echo ========================================
echo  Starting Aarambha PMS Desktop App
echo ========================================
echo.

echo [1/2] Starting Backend Server...
start cmd /k "cd ..\backend && node server.js"

timeout /t 3

echo [2/2] Launching Desktop Application...
python main.py

pause
