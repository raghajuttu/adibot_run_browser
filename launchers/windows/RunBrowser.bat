@echo off
rem Double-click launcher for the Run Browser app (no console window).
rem Lives in launchers\windows\, so step up two levels to the project folder
rem before running the module.
cd /d "%~dp0..\.."

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw -m run_browser
    exit /b
)

rem Fall back to the Windows Python launcher's windowed variant.
where pyw >nul 2>&1
if %errorlevel%==0 (
    start "" pyw -3 -m run_browser
    exit /b
)

echo Could not find pythonw.exe on PATH.
echo Install Python 3.10+ from python.org and tick "Add Python to PATH",
echo or run the app from a terminal with:  python -m run_browser
pause
