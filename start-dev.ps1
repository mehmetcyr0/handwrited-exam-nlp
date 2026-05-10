# El Yazısı Sınav Okuyucu — backend (8000) + frontend (5173)
# Çalıştırma: sağ tık → "PowerShell ile çalıştır" veya: powershell -ExecutionPolicy Bypass -File .\start-dev.ps1

$ErrorActionPreference = "Stop"
$root = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

if (-not (Test-Path $backend)) {
    Write-Error "backend bulunamadı: $backend"
    exit 1
}
if (-not (Test-Path $frontend)) {
    Write-Error "frontend bulunamadı: $frontend"
    exit 1
}

Push-Location $backend
try {
    if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
        Write-Host "Python sanal ortam oluşturuluyor..."
        py -3 -m venv .venv 2>$null
        if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
            python -m venv .venv
        }
    }
    Write-Host "pip install -r requirements.txt (ilk kurulum birkaç dakika sürebilir)..."
    & ".\.venv\Scripts\pip.exe" install --no-cache-dir -r requirements.txt
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "İki CMD penceresi açılıyor: API http://127.0.0.1:8000 | Arayüz http://127.0.0.1:5173"
Write-Host ""

# -WorkingDirectory: cd ve tirnak hatasi olmadan (Turkce yol, bosluk)
$backLine = ".venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000"
Start-Process cmd.exe -WorkingDirectory $backend -ArgumentList "/k", $backLine

$frontLine = "if not exist node_modules\ npm install && npm run dev -- --host 127.0.0.1"
Start-Process cmd.exe -WorkingDirectory $frontend -ArgumentList "/k", $frontLine
