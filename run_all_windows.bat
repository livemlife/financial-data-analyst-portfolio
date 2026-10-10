@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Setup is incomplete. Double-click setup_windows.bat first.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" run_all.py
if errorlevel 1 (
  echo.
  echo [ERROR] Analysis stopped. Please copy the message above when asking for help.
  pause
  exit /b 1
)

echo.
echo Completed. Open each project's outputs folder.
start "" "01_transaction_risk\outputs\summary.html"
start "" "02_customer_profitability\outputs\summary.html"
start "" "03_credit_early_warning\outputs\summary.html"
pause
