@echo off
chcp 65001 >nul
echo 8000 ve 5173 portlarindaki surecler kapatiliyor...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ports=8000,5173; foreach($p in $ports){ Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | ForEach-Object { $id=$_.OwningProcess; if($id){ Write-Host (' PID ' + $id + ' (port ' + $p + ')'); Stop-Process -Id $id -Force -ErrorAction SilentlyContinue } } }"
echo Tamam.
pause
