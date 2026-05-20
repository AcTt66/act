# Frontend Connection Diagnostic

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Frontend Connection Diagnostic" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Frontend (5178)
Write-Host "[1] Checking Frontend (port 5178)..." -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:5178" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "    [OK] Frontend is running" -ForegroundColor Green
} catch {
    Write-Host "    [X] Frontend NOT running on port 5178" -ForegroundColor Red
}

# Check Backend (8012)
Write-Host "[2] Checking Backend (port 8012)..." -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8012/api/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "    [OK] Backend is running" -ForegroundColor Green
} catch {
    Write-Host "    [X] Backend NOT running on port 8012" -ForegroundColor Red
    Write-Host "    Start backend: cd backend; python main.py" -ForegroundColor Yellow
}

# Check ports
Write-Host "[3] Port Status:" -ForegroundColor Cyan
foreach ($port in @(5178, 8012)) {
    $c = Get-NetTCPConnection -LocalPort $port -EA SilentlyContinue
    if ($c) {
        $p = Get-Process -Id $c[0].OwningProcess -EA SilentlyContinue
        Write-Host "    Port $port : $($p.ProcessName)" -ForegroundColor Yellow
    } else {
        Write-Host "    Port $port : Available" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "To start system, run in 2 terminals:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Terminal 1:" -ForegroundColor Cyan
Write-Host "  cd d:\BaiduNetdiskDownload\医路通Agent_Pro\backend" -ForegroundColor White
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 2:" -ForegroundColor Cyan
Write-Host "  cd d:\BaiduNetdiskDownload\医路通Agent_Pro\frontend" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Then access: http://127.0.0.1:5178" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
