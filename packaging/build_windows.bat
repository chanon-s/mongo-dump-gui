@echo off
echo =======================================================
echo Building Portable MongoDB Dump GUI for Windows x86_64
echo =======================================================

REM Ensure we run from the project root
cd /d "%~dp0\.."

REM Activate virtualenv if present
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Clean previous builds
if exist dist\MongoDumpGUI rmdir /s /q dist\MongoDumpGUI
if exist dist\MongoDumpGUI.exe del /f /q dist\MongoDumpGUI.exe
if exist build rmdir /s /q build

echo Installing / verifying requirements...
pip install -r requirements.txt

echo Running PyInstaller...
REM Build portable single executable
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "MongoDumpGUI" ^
    --collect-all customtkinter ^
    app.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo BUILD SUCCESSFUL!
    echo Portable executable is ready at: dist\MongoDumpGUI.exe
    echo You can move this single .exe file anywhere and run it.
    echo =======================================================
) else (
    echo.
    echo [ERROR] Build failed! Check the console output above.
)

pause
