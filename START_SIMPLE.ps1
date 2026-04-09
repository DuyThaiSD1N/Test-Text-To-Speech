# Script khởi động Simple Voice Agent
Write-Host "=== KHỞI ĐỘNG SIMPLE VOICE AGENT ===" -ForegroundColor Cyan

# Dừng port 8002
Write-Host "`nDừng tiến trình cũ..." -ForegroundColor Yellow
$process = Get-NetTCPConnection -LocalPort 8002 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($process) {
    foreach ($pid in $process) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

Write-Host "`nKhởi động server..." -ForegroundColor Green
Write-Host "Truy cập: http://localhost:8002" -ForegroundColor White
Write-Host "Nhấn Ctrl+C để dừng`n" -ForegroundColor Yellow

python simple_server.py
