@echo off
chcp 65001 >nul
set "ROOT=%~dp0"
set "BACK=%ROOT%backend"
set "FRONT=%ROOT%frontend"

if not exist "%BACK%\main.py" (
  echo backend bulunamadi: %BACK%
  pause
  exit /b 1
)

cd /d "%BACK%"
if not exist ".venv\Scripts\python.exe" (
  echo venv olusturuluyor...
  py -3 -m venv .venv 2>nul
  if not exist ".venv\Scripts\python.exe" python -m venv .venv
)
echo pip install...
call ".venv\Scripts\pip.exe" install --no-cache-dir -r requirements.txt
if errorlevel 1 (
  echo.
  echo pip hatasi. Bozuk kurulum olabilir: backend\reset-venv.cmd calistirin, sonra run-all.cmd tekrar.
  pause
  exit /b 1
)

echo.
echo API: http://127.0.0.1:8000  ^| Arayuz: http://127.0.0.1:5173
echo Iki pencere aciliyor. Kapatmak icin pencereleri kapatin.
echo.

start "ElYazisi-API" cmd /k "cd /d \"%BACK%\" && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000"

cd /d "%FRONT%"
if not exist "node_modules\" call npm install
start "ElYazisi-UI" cmd /k "cd /d \"%FRONT%\" && npm run dev"
