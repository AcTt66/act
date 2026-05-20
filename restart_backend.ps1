# Restart Backend Script

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Restarting Backend Service" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Stop any existing backend processes
Write-Host "[1/3] Stopping existing backend processes..." -ForegroundColor Yellow
$backendProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*main.py*" }
if ($backendProcesses) {
    $backendProcesses | Stop-Process -Force
    Write-Host "    Stopped $($backendProcesses.Count) process(es)" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "    No backend processes found" -ForegroundColor Gray
}

# Check port 8012
Write-Host "[2/3] Checking port 8012..." -ForegroundColor Yellow
$portCheck = Get-NetTCPConnection -LocalPort 8012 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "    Port still in use, waiting..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    $portCheck = Get-NetTCPConnection -LocalPort 8012 -ErrorAction SilentlyContinue
    if ($portCheck) {
        $proc = Get-Process -Id $portCheck[0].OwningProcess
        Write-Host "    Port occupied by: $($proc.ProcessName) (PID: $($portCheck[0].OwningProcess))" -ForegroundColor Red
        Write-Host "    Try: Stop-Process -Id $($portCheck[0].OwningProcess) -Force" -ForegroundColor Yellow
    }
} else {
    Write-Host "    Port 8012 is now free" -ForegroundColor Green
}

# Start backend
Write-Host "[3/3] Starting backend service..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting backend - a new window will open..." -ForegroundColor Cyan
Write-Host ""

# Start in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'd:\BaiduNetdiskDownload\医路通Agent_Pro\backend'; Write-Host 'Backend starting...'; python main.py" -WindowStyle Normal

# Wait for backend to start
Write-Host "Waiting for backend to start (5 seconds)..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Check if backend is running
Write-Host ""
Write-Host "Checking backend status..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8012/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "    [OK] Backend is running!" -ForegroundColor Green
    
    # Check settings
    Write-Host ""
    Write-Host "Checking settings..." -ForegroundColor Yellow
    $settings = Invoke-RestMethod -Uri "http://127.0.0.1:8012/api/settings" -TimeoutSec 5
    Write-Host "    LLM Enabled: $($settings.llm_enabled)" -ForegroundColor $(if ($settings.llm_enabled) { "Green" } else { "Red" })
    Write-Host "    API Key Configured: $($settings.api_key_configured)" -ForegroundColor $(if ($settings.api_key_configured) { "Green" } else { "Red" })
    Write-Host "    Model: $($settings.model_name)" -ForegroundColor White
    Write-Host "    Base URL: $($settings.base_url)" -ForegroundColor White
    
    if ($settings.llm_enabled) {
        Write-Host ""
        Write-Host "================================================" -ForegroundColor Green
        Write-Host "   Remote Model is now ENABLED!" -ForegroundColor Green
        Write-Host "================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Please refresh your browser page!" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "WARNING: LLM is still disabled. Please check config.yaml" -ForegroundColor Red
    }
} catch {
    Write-Host "    [X] Backend not responding yet" -ForegroundColor Red
    Write-Host "    Please check the backend window" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Access the app at: http://127.0.0.1:5178" -ForegroundColor Cyan
Write-Host ""
