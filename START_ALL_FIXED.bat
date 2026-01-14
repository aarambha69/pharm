@echo off
echo ========================================
echo  Starting Aarambha PMS (Fixed Launcher)
echo ========================================
echo.

echo [1/3] Starting Backend Server (Port 5000)...
start "Aarambha Backend" cmd /k "cd /d "%~dp0backend" && node server.js"

echo Waiting for backend to initialize...
timeout /t 5

echo [2/3] Starting Frontend (Port 3000)...
start "Aarambha Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [3/3] Launching Desktop Application...
cd /d "%~dp0"
call .venv\Scripts\activate
start "Aarambha Desktop" python DesktopApp/main.py

echo.
echo All systems launched.
echo Backend: Port 5000
echo Frontend: Port 3000
echo.
pause
