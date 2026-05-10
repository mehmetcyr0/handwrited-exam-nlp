@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [.venv yok] Sanal ortam olusturuluyor...
  py -3 -m venv .venv 2>nul
  if not exist ".venv\Scripts\python.exe" python -m venv .venv
  echo pip install -r requirements.txt ^(ilk sefer uzun surebilir^)...
  call ".venv\Scripts\pip.exe" install --no-cache-dir -r requirements.txt
  if errorlevel 1 (
    echo pip basarisiz.
    pause
    exit /b 1
  )
)

echo.
echo API: http://127.0.0.1:8000/docs
echo Kapatmak icin Ctrl+C
echo.

".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
