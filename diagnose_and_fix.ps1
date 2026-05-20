# 医路通 Agent Pro - 问题诊断与修复脚本

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   医路通 Agent Pro - 问题诊断与修复工具" -ForegroundColor Cyan
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

function Test-LLMAPI {
    param($apiKey, $baseUrl, $modelName)
    
    try {
        $headers = @{
            "Authorization" = $apiKey
            "Content-Type" = "application/json"
        }
        
        $body = @{
            model = $modelName
            messages = @(@{role = "user"; content = "test"})
            max_tokens = 10
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$baseUrl/chat/completions" `
            -Method Post `
            -Headers $headers `
            -Body $body `
            -ContentType "application/json" `
            -TimeoutSec 30
        
        return @{Success = $true; Response = $response}
    } catch {
        return @{Success = $false; Error = $_.Exception.Message}
    }
}

# 1. 检查后端服务状态
Write-Host "[1/6] 检查后端服务状态..." -ForegroundColor Cyan
if (Test-BackendConnection) {
    Write-Host "    [OK] 后端服务正在运行" -ForegroundColor Green
} else {
    Write-Host "    [X] 后端服务未运行" -ForegroundColor Red
    Write-Host ""
    Write-Host "    请先启动后端服务：" -ForegroundColor Yellow
    Write-Host "      cd backend" -ForegroundColor White
    Write-Host "      python main.py" -ForegroundColor White
    Write-Host ""
}

# 2. 检查配置文件
Write-Host "[2/6] 检查配置文件..." -ForegroundColor Cyan
$configPath = "backend\config\config.yaml"
if (Test-Path $configPath) {
    Write-Host "    [OK] 配置文件存在" -ForegroundColor Green
    
    # 读取配置
    $config = Get-Content $configPath -Raw | ConvertFrom-Yaml
    
    Write-Host "    LLM API Key: $($config.llm.api_key.Substring(0, [Math]::Min(20, $config.llm.api_key.Length)))..." -ForegroundColor White
    Write-Host "    LLM Base URL: $($config.llm.base_url)" -ForegroundColor White
    Write-Host "    LLM Model: $($config.llm.model_name)" -ForegroundColor White
    Write-Host "    LLM Enabled: $($config.features.enable_llm)" -ForegroundColor White
} else {
    Write-Host "    [X] 配置文件不存在" -ForegroundColor Red
}

# 3. 测试 LLM API 连接
Write-Host "[3/6] 测试 LLM API 连接..." -ForegroundColor Cyan
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Yaml
    $result = Test-LLMAPI -apiKey $config.llm.api_key -baseUrl $config.llm.base_url -modelName $config.llm.model_name
    
    if ($result.Success) {
        Write-Host "    [OK] LLM API 连接成功" -ForegroundColor Green
        Write-Host "    模型响应: $($result.Response.choices[0].message.content)" -ForegroundColor White
    } else {
        Write-Host "    [X] LLM API 连接失败" -ForegroundColor Red
        Write-Host "    错误: $($result.Error)" -ForegroundColor Red
        
        # 提供具体的解决方案
        if ($result.Error -like "*401*") {
            Write-Host ""
            Write-Host "    [建议] API Key 可能已过期或无效" -ForegroundColor Yellow
            Write-Host "    请访问 DMXAPI 官网更新 API Key" -ForegroundColor Yellow
        } elseif ($result.Error -like "*connection*") {
            Write-Host ""
            Write-Host "    [建议] 无法连接到远程服务器" -ForegroundColor Yellow
            Write-Host "    请检查网络连接或防火墙设置" -ForegroundColor Yellow
        }
    }
}

# 4. 检查端口占用
Write-Host "[4/6] 检查端口占用情况..." -ForegroundColor Cyan
$backendPort = Get-NetTCPConnection -LocalPort 8012 -ErrorAction SilentlyContinue
$frontendPort = Get-NetTCPConnection -LocalPort 5178 -ErrorAction SilentlyContinue

if ($backendPort) {
    $process = Get-Process -Id $backendPort[0].OwningProcess -ErrorAction SilentlyContinue
    Write-Host "    后端端口 (8012): 被进程 $($process.ProcessName) (PID: $($backendPort[0].OwningProcess)) 占用" -ForegroundColor Yellow
} else {
    Write-Host "    后端端口 (8012): 可用" -ForegroundColor Green
}

if ($frontendPort) {
    $process = Get-Process -Id $frontendPort[0].OwningProcess -ErrorAction SilentlyContinue
    Write-Host "    前端端口 (5178): 被进程 $($process.ProcessName) (PID: $($frontendPort[0].OwningProcess)) 占用" -ForegroundColor Yellow
} else {
    Write-Host "    前端端口 (5178): 可用" -ForegroundColor Green
}

# 5. 检查依赖
Write-Host "[5/6] 检查依赖安装..." -ForegroundColor Cyan
$backendDeps = @("fastapi", "uvicorn", "httpx", "pydantic")
$missingBackend = @()

foreach ($dep in $backendDeps) {
    $installed = pip show $dep 2>&1 | Select-String "Name: $dep"
    if ($installed) {
        Write-Host "    [OK] $dep" -ForegroundColor Green
    } else {
        Write-Host "    [X] $dep 未安装" -ForegroundColor Red
        $missingBackend += $dep
    }
}

if ($missingBackend.Count -gt 0) {
    Write-Host ""
    Write-Host "    安装缺失的依赖..." -ForegroundColor Yellow
    pip install $missingBackend -q
}

# 6. 环境变量检查
Write-Host "[6/6] 检查环境变量..." -ForegroundColor Cyan
$envVars = @("MEDIX_API_KEY", "MEDIX_BASE_URL", "MEDIX_MODEL_NAME")
foreach ($var in $envVars) {
    $value = [System.Environment]::GetEnvironmentVariable($var)
    if ($value) {
        Write-Host "    $var = $value" -ForegroundColor Yellow
    } else {
        Write-Host "    $var = (未设置，使用配置文件)" -ForegroundColor Green
    }
}

# 总结和建议
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   诊断完成" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()

# 检查后端
if (-not (Test-BackendConnection)) {
    $issues += "后端服务未运行"
}

# 检查配置
if (-not (Test-Path $configPath)) {
    $issues += "配置文件缺失"
}

# 测试API
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Yaml
    $result = Test-LLMAPI -apiKey $config.llm.api_key -baseUrl $config.llm.base_url -modelName $config.llm.model_name
    if (-not $result.Success) {
        $issues += "LLM API 连接失败"
    }
}

if ($issues.Count -eq 0) {
    Write-Host "所有检查通过！系统应该正常运行。" -ForegroundColor Green
    Write-Host ""
    Write-Host "如果仍有问题，请尝试：" -ForegroundColor Yellow
    Write-Host "  1. 重启后端服务 (Ctrl+C 停止后重新启动)" -ForegroundColor White
    Write-Host "  2. 重启前端服务 (Ctrl+C 停止后重新启动)" -ForegroundColor White
    Write-Host "  3. 清除浏览器缓存并刷新页面" -ForegroundColor White
    Write-Host "  4. 尝试使用隐身/无痕模式打开浏览器" -ForegroundColor White
} else {
    Write-Host "发现问题：" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "请根据上述建议修复问题后重新运行此脚本。" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "详细启动指南请查看: STARTUP_GUIDE.md" -ForegroundColor Cyan
Write-Host ""

Read-Host "按 Enter 退出"
