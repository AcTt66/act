# 医路通 Agent Pro - PowerShell 启动脚本

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   医路通 Agent Pro - 一键启动工具" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] 检测到 Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    Write-Host "下载地址：https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

# 检查目录
if (-not (Test-Path "backend\config\config.yaml")) {
    Write-Host "[错误] 找不到后端配置文件" -ForegroundColor Red
    Write-Host "请确保在项目根目录运行此脚本" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

if (-not (Test-Path "frontend\package.json")) {
    Write-Host "[错误] 找不到前端配置文件" -ForegroundColor Red
    Write-Host "请确保在项目根目录运行此脚本" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

Write-Host "[1/4] 检查后端依赖..." -ForegroundColor Cyan
Set-Location backend
if (-not (pip show fastapi 2>&1 | Select-String "Name:")) {
    Write-Host "    安装后端依赖中..." -ForegroundColor Yellow
    pip install -r requirements.txt -q
}
Set-Location ..

Write-Host "[2/4] 检查前端依赖..." -ForegroundColor Cyan
Set-Location frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "    安装前端依赖中（首次可能需要几分钟）..." -ForegroundColor Yellow
    npm install --silent
}
Set-Location ..

Write-Host "[3/4] 启动后端服务..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; python main.py" -WindowStyle Normal

Write-Host ""
Write-Host "[4/4] 等待后端启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   启动完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   后端服务: http://127.0.0.1:8012" -ForegroundColor Yellow
Write-Host "   前端服务: http://127.0.0.1:5178" -ForegroundColor Yellow
Write-Host ""
Write-Host "   正在启动前端服务..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 启动前端服务
Set-Location frontend
npm run dev
