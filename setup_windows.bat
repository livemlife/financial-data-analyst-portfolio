@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY_CMD=py"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python 3.11 or later from python.org.
    pause
    exit /b 1
  )
  set "PY_CMD=python"
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating a virtual environment...
  %PY_CMD% -m venv .venv
  if errorlevel 1 goto :fail
)

echo Installing required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo Setup completed. Double-click run_all_windows.bat next.
pause
exit /b 0

:fail
echo.
echo [ERROR] Setup failed. Please copy the message above when asking for help.
pause
exit /b 1

