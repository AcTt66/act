# Yilutong Agent Pro - Admin System Diagnostic Tool

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Admin System Diagnosis Tool" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking system components..." -ForegroundColor Yellow
Write-Host ""

# Check main backend (8012)
Write-Host "[1/3] Checking main backend service (port 8012)..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8012/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "    [OK] Main backend is running on port 8012" -ForegroundColor Green
} catch {
    Write-Host "    [X] Main backend is NOT running on port 8012" -ForegroundColor Red
    Write-Host "    This is required for admin system to work!" -ForegroundColor Yellow
    Write-Host ""
}

# Check admin backend (8022)
Write-Host "[2/3] Checking admin system service (port 8022)..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8022/" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "    [OK] Admin system is running on port 8022" -ForegroundColor Green
} catch {
    Write-Host "    [X] Admin system is NOT running on port 8022" -ForegroundColor Red
    Write-Host "    Please start admin system first:" -ForegroundColor Yellow
    Write-Host "      cd admin_system" -ForegroundColor White
    Write-Host "      .\start_admin_backend.ps1" -ForegroundColor White
    Write-Host ""
}

# Check ports
Write-Host "[3/3] Checking port usage..." -ForegroundColor Cyan
$ports = @(8012, 8022, 5178)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        $process = Get-Process -Id $connections[0].OwningProcess -ErrorAction SilentlyContinue
        Write-Host "    Port $port : In use by $($process.ProcessName)" -ForegroundColor Yellow
    } else {
        Write-Host "    Port $port : Available" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Recommended Startup Steps" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You need to run THREE separate terminals:" -ForegroundColor Yellow
Write-Host ""
Write-Host "TERMINAL 1 - Main Backend:" -ForegroundColor Cyan
Write-Host "  cd d:\BaiduNetdiskDownload\医路通Agent_Pro\backend" -ForegroundColor White
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""
Write-Host "TERMINAL 2 - Admin System:" -ForegroundColor Cyan
Write-Host "  cd d:\BaiduNetdiskDownload\医路通Agent_Pro" -ForegroundColor White
Write-Host "  cd admin_system" -ForegroundColor White
Write-Host "  .\start_admin_backend.ps1" -ForegroundColor White
Write-Host ""
Write-Host "TERMINAL 3 - Frontend (optional):" -ForegroundColor Cyan
Write-Host "  cd d:\BaiduNetdiskDownload\医路通Agent_Pro\frontend" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  Main App:     http://127.0.0.1:5178" -ForegroundColor White
Write-Host "  Admin Panel:  http://127.0.0.1:8022" -ForegroundColor White
Write-Host ""

# Test admin login
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Testing Admin Login" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Default credentials
$username = "admin"
$password = "admin123"

Write-Host "Testing login with default credentials..." -ForegroundColor Yellow
Write-Host "  Username: $username" -ForegroundColor White
Write-Host "  Password: $password" -ForegroundColor White
Write-Host ""

try {
    $body = @{
        username = $username
        password = $password
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8022/api/admin/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    if ($response.ok) {
        Write-Host "    [OK] Login successful!" -ForegroundColor Green
        Write-Host "    Session: $($response.session.Substring(0, 20))..." -ForegroundColor White
    }
} catch {
    Write-Host "    [X] Login failed" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "    If you see 401 error:" -ForegroundColor Yellow
    Write-Host "    Please set credentials when starting admin system:" -ForegroundColor Yellow
    Write-Host '      $env:MEDIX_ADMIN_USERNAME="admin"' -ForegroundColor White
    Write-Host '      $env:MEDIX_ADMIN_PASSWORD="your_password"' -ForegroundColor White
    Write-Host '      .\start_admin_backend.ps1' -ForegroundColor White
}

Write-Host ""
Write-Host "For detailed guide, see: STARTUP_GUIDE.md" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
