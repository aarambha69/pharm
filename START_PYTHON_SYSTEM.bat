@echo off
echo Starting Aarambha Pharmacy System (Python Version)...

:: Start Backend (Node.js)
start "Aarambha Backend" cmd /k "cd backend && node server.js"

:: Start Frontend (Web Interface - Optional)
start "Aarambha Web" cmd /k "cd frontend && npm run dev"

echo Waiting for backend to initialize...
timeout /t 5

:: Start Python Desktop App
echo Starting Desktop App (using .venv)...
start "Aarambha Desktop" cmd /k "call .venv\Scripts\activate.bat && python DesktopApp/main.py"

echo System launching...
pause
