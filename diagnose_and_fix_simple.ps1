# Yilutong Agent Pro - Problem Diagnosis Script

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Yilutong Agent Pro - Problem Diagnosis Tool" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

function Test-BackendConnection {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8012/api/health" -TimeoutSec 5 -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# 1. Check backend service
Write-Host "[1/4] Checking backend service..." -ForegroundColor Cyan
if (Test-BackendConnection) {
    Write-Host "    [OK] Backend service is running" -ForegroundColor Green
} else {
    Write-Host "    [X] Backend service is NOT running" -ForegroundColor Red
    Write-Host ""
    Write-Host "    Please start backend first:" -ForegroundColor Yellow
    Write-Host "      cd backend" -ForegroundColor White
    Write-Host "      python main.py" -ForegroundColor White
    Write-Host ""
}

# 2. Check port usage
Write-Host "[2/4] Checking port usage..." -ForegroundColor Cyan
$backendPort = Get-NetTCPConnection -LocalPort 8012 -ErrorAction SilentlyContinue
$frontendPort = Get-NetTCPConnection -LocalPort 5178 -ErrorAction SilentlyContinue

if ($backendPort) {
    $process = Get-Process -Id $backendPort[0].OwningProcess -ErrorAction SilentlyContinue
    Write-Host "    Backend port (8012): In use by $($process.ProcessName)" -ForegroundColor Yellow
} else {
    Write-Host "    Backend port (8012): Available" -ForegroundColor Green
}

if ($frontendPort) {
    $process = Get-Process -Id $frontendPort[0].OwningProcess -ErrorAction SilentlyContinue
    Write-Host "    Frontend port (5178): In use by $($process.ProcessName)" -ForegroundColor Yellow
} else {
    Write-Host "    Frontend port (5178): Available" -ForegroundColor Green
}

# 3. Check dependencies
Write-Host "[3/4] Checking dependencies..." -ForegroundColor Cyan
$backendDeps = @("fastapi", "uvicorn", "httpx", "pydantic")
$missingBackend = @()

foreach ($dep in $backendDeps) {
    $installed = pip show $dep 2>&1 | Select-String "Name: $dep"
    if ($installed) {
        Write-Host "    [OK] $dep" -ForegroundColor Green
    } else {
        Write-Host "    [X] $dep - NOT installed" -ForegroundColor Red
        $missingBackend += $dep
    }
}

if ($missingBackend.Count -gt 0) {
    Write-Host ""
    Write-Host "    Installing missing dependencies..." -ForegroundColor Yellow
    pip install $missingBackend -q
    Write-Host "    [OK] Dependencies installed" -ForegroundColor Green
}

# 4. Check configuration
Write-Host "[4/4] Checking configuration..." -ForegroundColor Cyan
$configPath = "backend\config\config.yaml"
if (Test-Path $configPath) {
    Write-Host "    [OK] Configuration file exists" -ForegroundColor Green
} else {
    Write-Host "    [X] Configuration file NOT found" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Diagnosis Complete" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()

if (-not (Test-BackendConnection)) {
    $issues += "Backend service is not running"
}

if (-not (Test-Path $configPath)) {
    $issues += "Configuration file missing"
}

if ($issues.Count -eq 0) {
    Write-Host "All checks passed! System should be working." -ForegroundColor Green
    Write-Host ""
    Write-Host "If you still have problems, try:" -ForegroundColor Yellow
    Write-Host "  1. Restart backend service" -ForegroundColor White
    Write-Host "  2. Restart frontend service" -ForegroundColor White
    Write-Host "  3. Clear browser cache and refresh" -ForegroundColor White
    Write-Host "  4. Try incognito/private mode" -ForegroundColor White
} else {
    Write-Host "Issues found:" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "For detailed startup guide, see: STARTUP_GUIDE.md" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
