@echo off
chcp 65001 >nul
echo 🚀 启动 TailAdmin React 数据分析系统
echo ===========================================

REM 检查目录
if not exist "backend\app.py" (
    echo ❌ 错误: 请在项目根目录运行此脚本
    echo 当前目录: %CD%
    echo 应该包含 backend\ 和 frontend\ 目录
    pause
    exit /b 1
)

echo 📡 启动后端 Flask 服务器...
start "后端服务" cmd /k "cd /d %CD%\backend && python app.py"

echo ⏳ 等待后端服务启动...
timeout /t 3 /nobreak >nul

echo 🎨 启动前端 React 开发服务器...
start "前端服务" cmd /k "cd /d %CD%\frontend && npm run dev"

echo ⏳ 等待前端服务启动...
timeout /t 5 /nobreak >nul

echo.
echo ✅ 服务启动完成!
echo ===========================================
echo 📡 后端 API: http://localhost:5000
echo 🎨 前端界面: http://localhost:5173
echo.
echo 💡 提示:
echo   - 前端会自动在浏览器中打开
echo   - 关闭命令行窗口会停止对应服务
echo.

REM 尝试打开浏览器
start "" "http://localhost:5173"
echo 🌐 已在默认浏览器中打开前端界面

echo.
echo 按任意键退出此脚本 (服务将继续在后台运行)...
pause >nul