@echo off
setlocal
echo ===================================================
echo   AARAMBHA PHARMACY SOFTWARE - PRODUCTION BUILD
echo ===================================================

echo [1/5] Setting up Environment...
set "PROJECT_ROOT=%~dp0"
if exist "%PROJECT_ROOT%.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%PROJECT_ROOT%.venv\Scripts\python.exe"
    set "PIP_CMD=%PROJECT_ROOT%.venv\Scripts\pip.exe"
) else (
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
)

echo [2/5] Installing Dependencies...
REM "%PIP_CMD%" install -r "%PROJECT_ROOT%DesktopApp\requirements.txt"
REM "%PIP_CMD%" install pyinstaller

echo [3/5] Building Desktop Application...
cd "%PROJECT_ROOT%DesktopApp"
"%PYTHON_CMD%" -m PyInstaller AarambhaPMS.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo BUILD FAILED!
    cd ..
    exit /b %errorlevel%
)
cd ..

echo [4/5] Bundling Backend System...
if not exist "%PROJECT_ROOT%DesktopApp\dist\AarambhaPMS_Client\backend" mkdir "%PROJECT_ROOT%DesktopApp\dist\AarambhaPMS_Client\backend"
xcopy "%PROJECT_ROOT%backend" "%PROJECT_ROOT%DesktopApp\dist\AarambhaPMS_Client\backend" /E /I /Y /EXCLUDE:exclude_list.txt

REM Manually copy .env because xcopy might miss it or it might be needed explicitly
copy "%PROJECT_ROOT%backend\.env" "%PROJECT_ROOT%DesktopApp\dist\AarambhaPMS_Client\backend\.env"

echo [5/5] Installing Backend Dependencies...
cd "%PROJECT_ROOT%DesktopApp\dist\AarambhaPMS_Client\backend"
call npm install --production
cd ../../../..

echo [6/6] Creating Database Setup Script...
echo node backend/setup_complete_db.js > "%PROJECT_ROOT%DesktopApp\dist\AarambhaPMS_Client\SETUP_DB.bat"

echo.
echo ===================================================
echo   BUILD SUCCESSFUL!
echo   Output Location: DesktopApp\dist\AarambhaPMS_Client
echo ===================================================
exit /b 0
