@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\pip.exe" (
  echo Once sanal ortam olusturun: py -3 -m venv .venv
  pause
  exit /b 1
)

echo Onceki PyTorch kaldiriliyor...
call ".venv\Scripts\pip.exe" uninstall -y torch torchvision torchaudio 2>nul

echo.
echo [1/2] Resmi CPU haznesi: download.pytorch.org ...
call ".venv\Scripts\pip.exe" install --no-cache-dir torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
  echo.
  echo [2/2] PyPI uzerinden torch==2.4.1 ...
  call ".venv\Scripts\pip.exe" install --no-cache-dir "torch==2.4.1"
)

if errorlevel 1 (
  echo.
  echo pip basarisiz. VC++ x64: https://aka.ms/vs/17/release/vc_redist.x64.exe
  echo Not: API yine de calisir; puanlama otomatik TF-IDF moduna duser.
  pause
  exit /b 1
)

echo.
echo Tamam. Test: .venv\Scripts\python.exe -c "import torch; print(torch.__version__)"
echo Sorun surerse torch'u silip API'yi calistirin — TF-IDF yedek devreye girer.
pause
