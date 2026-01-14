@echo off
echo ========================================
echo  Aarambha PMS - Desktop App Builder
echo ========================================
echo.

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [2/3] Building standalone .exe file...
pyinstaller --onefile --windowed --name="AarambhaPMS" --icon=icon.ico main.py

echo.
echo [3/3] Build complete!
echo.
echo Your .exe file is located at: dist\AarambhaPMS.exe
echo.
pause
