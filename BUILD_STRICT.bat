@echo off
setlocal
echo ===================================================
echo   STRICT PRODUCTION BUILD (Python 3.13)
echo ===================================================

set "PROJECT_ROOT=%~dp0"
set "DIST_DIR=%PROJECT_ROOT%DesktopApp\dist"
cd "%PROJECT_ROOT%DesktopApp"

echo [1/6] Cleaning Previous Builds...
rmdir /s /q "%DIST_DIR%" 2>nul
rmdir /s /q "build" 2>nul

echo [2/6] Upgrading Build Tools...
call ..\.venv\Scripts\python.exe -m pip install --upgrade pip pyinstaller

echo [3/6] Building with PyInstaller (Onedir mode)...
call ..\.venv\Scripts\python.exe -m PyInstaller AarambhaPMS.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo BUILD FAILED!
    exit /b 1
)

echo [4/6] Verifying Critical DLLs...
if exist "%DIST_DIR%\AarambhaPMS_Client\_internal\python313.dll" (
    echo [OK] Internal Python313.dll found.
) else (
    echo [ERROR] python313.dll MISSING from _internal!
    exit /b 1
)

if exist "%DIST_DIR%\AarambhaPMS_Client\AarambhaPMS.exe" (
    echo [OK] Executable found.
) else (
    echo [ERROR] Executable MISSING!
    exit /b 1
)

echo [5/6] Copying Backend...
cd ..
if not exist "%DIST_DIR%\AarambhaPMS_Client\backend" mkdir "%DIST_DIR%\AarambhaPMS_Client\backend"
xcopy "backend" "%DIST_DIR%\AarambhaPMS_Client\backend" /E /I /Y /EXCLUDE:exclude_list.txt
copy "backend\.env" "%DIST_DIR%\AarambhaPMS_Client\backend\.env"

echo [6/6] Zipping Distribution...
powershell Compress-Archive -Path "%DIST_DIR%\AarambhaPMS_Client" -DestinationPath "%DIST_DIR%\AarambhaPMS_DIST.zip" -Force

echo.
echo ===================================================
echo   BUILD COMPLETE: DesktopApp\dist\AarambhaPMS_DIST.zip
echo ===================================================
exit /b 0
