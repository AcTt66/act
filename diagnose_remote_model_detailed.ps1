# Yilutong Agent Pro - Remote Model Diagnostic Tool

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Remote Model Call Diagnostic Tool" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
Write-Host "[1/5] Checking backend service..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8012/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "    [OK] Backend is running" -ForegroundColor Green
    $backendRunning = $true
} catch {
    Write-Host "    [X] Backend is NOT running" -ForegroundColor Red
    Write-Host "    Please start backend first: python main.py" -ForegroundColor Yellow
    $backendRunning = $false
}

Write-Host ""

# Check configuration
Write-Host "[2/5] Checking configuration..." -ForegroundColor Cyan
$configPath = "backend\config\config.yaml"
if (Test-Path $configPath) {
    Write-Host "    [OK] Configuration file exists" -ForegroundColor Green
} else {
    Write-Host "    [X] Configuration file NOT found" -ForegroundColor Red
    exit 1
}

# Read and display key config
try {
    $configContent = Get-Content $configPath -Raw
    $apiKey = if ($configContent -match 'api_key:\s*"?([^"\n]+)"?') { $matches[1].Substring(0, [Math]::Min(15, $matches[1].Length)) + "..." } else { "NOT FOUND" }
    $baseUrl = if ($configContent -match 'base_url:\s*"?([^"\n]+)"?') { $matches[1] } else { "NOT FOUND" }
    $modelName = if ($configContent -match 'model_name:\s*"?([^"\n]+)"?') { $matches[1] } else { "NOT FOUND" }
    
    Write-Host "    API Key: $apiKey" -ForegroundColor White
    Write-Host "    Base URL: $baseUrl" -ForegroundColor White
    Write-Host "    Model: $modelName" -ForegroundColor White
} catch {
    Write-Host "    [X] Failed to read configuration" -ForegroundColor Red
}

Write-Host ""

# Test direct API connection
Write-Host "[3/5] Testing direct API connection to DMXAPI..." -ForegroundColor Cyan
Write-Host "    This will make a real API call to test connectivity" -ForegroundColor Yellow
Write-Host ""

try {
    # Read config from file
    $configContent = Get-Content $configPath -Raw
    $apiKey = if ($configContent -match 'api_key:\s*"?([^"\n]+)"?') { $matches[1].Trim() } else { "" }
    $baseUrl = if ($configContent -match 'base_url:\s*"?([^"\n]+)"?') { $matches[1].Trim() } else { "https://www.dmxapi.cn/v1" }
    $modelName = if ($configContent -match 'model_name:\s*"?([^"\n]+)"?') { $matches[1].Trim() } else { "qwen-plus" }
    
    $url = "$baseUrl/chat/completions"
    
    Write-Host "    URL: $url" -ForegroundColor White
    Write-Host "    Model: $modelName" -ForegroundColor White
    Write-Host ""
    Write-Host "    Sending test request..." -ForegroundColor Yellow
    
    $headers = @{
        "Authorization" = $apiKey
        "Content-Type" = "application/json"
    }
    
    $body = @{
        model = $modelName
        messages = @(@{role = "user"; content = "Say 'API test successful' in Chinese"})
        max_tokens = 50
        temperature = 0.3
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body -ContentType "application/json" -TimeoutSec 30
    
    if ($response.choices) {
        Write-Host "    [OK] API call successful!" -ForegroundColor Green
        Write-Host "    Response: $($response.choices[0].message.content)" -ForegroundColor White
        $apiWorking = $true
    }
} catch {
    Write-Host "    [X] API call failed" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try to parse error response
    if ($_.Exception.Response) {
        $statusCode = [int]$_.Exception.Response.StatusCode
        Write-Host "    HTTP Status: $statusCode" -ForegroundColor Red
        
        if ($statusCode -eq 401) {
            Write-Host ""
            Write-Host "    [ISSUE] Authentication failed!" -ForegroundColor Yellow
            Write-Host "    Your API key may be invalid or expired." -ForegroundColor Yellow
            Write-Host "    Please check your DMXAPI account and update the key." -ForegroundColor Yellow
        } elseif ($statusCode -eq 403) {
            Write-Host ""
            Write-Host "    [ISSUE] Access forbidden!" -ForegroundColor Yellow
            Write-Host "    Your account may not have permission for this model." -ForegroundColor Yellow
        } elseif ($statusCode -eq 429) {
            Write-Host ""
            Write-Host "    [ISSUE] Rate limit exceeded!" -ForegroundColor Yellow
            Write-Host "    Too many requests. Please wait and try again." -ForegroundColor Yellow
        } elseif ($statusCode -ge 500) {
            Write-Host ""
            Write-Host "    [ISSUE] Server error on DMXAPI side" -ForegroundColor Yellow
            Write-Host "    DMXAPI service may be temporarily unavailable." -ForegroundColor Yellow
        }
    }
    
    $apiWorking = $false
}

Write-Host ""

# Test via backend
Write-Host "[4/5] Testing via backend service..." -ForegroundColor Cyan
if ($backendRunning) {
    try {
        Write-Host "    Testing LLM through backend..." -ForegroundColor Yellow
        
        # This will only work if we can access the backend
        $testResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8012/api/health" -TimeoutSec 5
        Write-Host "    Backend health: OK" -ForegroundColor Green
        
        # Note: We can't easily test LLM via HTTP without proper auth
        # The actual test would need to go through the chat API
        Write-Host "    [OK] Backend is accessible" -ForegroundColor Green
        Write-Host "    Note: Full LLM test requires frontend interaction" -ForegroundColor Yellow
    } catch {
        Write-Host "    [X] Backend test failed" -ForegroundColor Red
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "    [SKIP] Backend not running" -ForegroundColor Gray
}

Write-Host ""

# Check network connectivity
Write-Host "[5/5] Checking network connectivity..." -ForegroundColor Cyan
try {
    $testConnection = Test-NetConnection -ComputerName "www.dmxapi.cn" -Port 443 -WarningAction SilentlyContinue
    if ($testConnection.TcpTestSucceeded) {
        Write-Host "    [OK] Can reach DMXAPI server (port 443)" -ForegroundColor Green
    } else {
        Write-Host "    [X] Cannot reach DMXAPI server" -ForegroundColor Red
        Write-Host "    Please check your firewall and network settings" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    [X] Network test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Diagnostic Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($apiWorking -and $backendRunning) {
    Write-Host "Everything looks good! The remote model should work." -ForegroundColor Green
    Write-Host ""
    Write-Host "If you're still having issues, try:" -ForegroundColor Yellow
    Write-Host "  1. Restart backend: python main.py" -ForegroundColor White
    Write-Host "  2. Clear browser cache" -ForegroundColor White
    Write-Host "  3. Try incognito mode" -ForegroundColor White
} elseif ($apiWorking -and -not $backendRunning) {
    Write-Host "API is working, but backend is not running." -ForegroundColor Yellow
    Write-Host "Please start backend: python main.py" -ForegroundColor White
} else {
    Write-Host "Found issues with remote model configuration." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "  1. Update API key in backend/config/config.yaml" -ForegroundColor White
    Write-Host "  2. Check if DMXAPI account is active" -ForegroundColor White
    Write-Host "  3. Verify network connection" -ForegroundColor White
    Write-Host "  4. Check if model name is correct" -ForegroundColor White
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"
