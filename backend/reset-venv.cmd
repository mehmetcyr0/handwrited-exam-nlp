@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo === El Yazisi: .venv silinip sifirdan kurulacak ===
echo Kapat: Calisan uvicorn / python pencereleri (kilitleme olmasin).
echo.
pause

if exist ".venv" (
  echo Eski .venv kaldiriliyor...
  rmdir /s /q ".venv" 2>nul
  if exist ".venv" (
    echo HATA: .venv silinemedi. Gorev Yoneticisinden python.exe kapatin, tekrar deneyin.
    pause
    exit /b 1
  )
)

echo Yeni sanal ortam...
py -3 -m venv .venv 2>nul
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if not exist ".venv\Scripts\python.exe" (
  echo python / py bulunamadi.
  pause
  exit /b 1
)

echo pip guncelleniyor...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools

echo requirements.txt kuruluyor (uzun surebilir)...
call ".venv\Scripts\pip.exe" install --no-cache-dir -r requirements.txt
if errorlevel 1 (
  echo pip hatasi.
  pause
  exit /b 1
)

echo.
echo Tamam. Simdi start-api.cmd veya ust klasorde run-all.cmd calistirin.
echo.
pause
