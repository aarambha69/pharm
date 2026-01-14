@echo off
echo Starting Aarambha Softwares PMS...

:: Start Backend
start cmd /k "cd backend && node server.js"

:: Start Frontend (Dev mode)
start cmd /k "cd frontend && npm run dev"

:: Start Desktop (Optional, after frontend is ready)
echo Waiting for frontend to start...
timeout /t 5
start cmd /k "cd desktop && npm start"

echo System handles are active.
echo Super Admin Login: 9855062769 / 987654321
pause
