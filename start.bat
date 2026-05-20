@echo off
chcp 65001 > nul
title 医路通 Agent Pro - 启动器

echo ================================================
echo    医路通 Agent Pro - 一键启动工具
echo ================================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查后端目录
if not exist "backend\config\config.yaml" (
    echo [错误] 找不到后端配置文件
    echo 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

:: 检查前端目录
if not exist "frontend\package.json" (
    echo [错误] 找不到前端配置文件
    echo 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

echo [1/4] 检查后端依赖...
cd backend
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo     安装后端依赖中...
    pip install -r requirements.txt -q
)
cd ..

echo [2/4] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo     安装前端依赖中（首次可能需要几分钟）...
    call npm install --silent
)
cd ..

echo [3/4] 启动后端服务...
start "后端服务 - 医路通Agent" cmd /k "cd /d %~dp0backend && python main.py"

echo.
echo [4/4] 等待后端启动...
timeout /t 5 /nobreak > nul

echo.
echo ================================================
echo    启动完成！
echo ================================================
echo.
echo    后端服务: http://127.0.0.1:8012
echo    前端服务: http://127.0.0.1:5178
echo.
echo    正在启动前端服务...
echo ================================================
echo.

:: 启动前端服务
cd frontend
call npm run dev

:: 如果前端启动失败，保持窗口
pause
