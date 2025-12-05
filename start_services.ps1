# TailAdmin React + Flask 后端启动脚本
# 使用方法: 在项目根目录运行 .\start_services.ps1

Write-Host "🚀 启动 TailAdmin React 数据分析系统" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan

# 检查是否在正确的目录
if (-not (Test-Path "backend\app.py") -or -not (Test-Path "frontend\package.json")) {
    Write-Host "❌ 错误: 请在项目根目录运行此脚本" -ForegroundColor Red
    Write-Host "当前目录: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "应该包含 backend/ 和 frontend/ 目录" -ForegroundColor Yellow
    exit 1
}

# 启动后端服务
Write-Host "📡 启动后端 Flask 服务器..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; python app.py"

# 等待后端启动
Write-Host "⏳ 等待后端服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 启动前端服务
Write-Host "🎨 启动前端 React 开发服务器..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

# 等待前端启动
Write-Host "⏳ 等待前端服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "" 
Write-Host "✅ 服务启动完成!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "📡 后端 API: http://localhost:5000" -ForegroundColor White
Write-Host "🎨 前端界面: http://localhost:5173" -ForegroundColor White
Write-Host "" 
Write-Host "💡 提示:" -ForegroundColor Yellow
Write-Host "  - 前端会自动在浏览器中打开" -ForegroundColor Gray
Write-Host "  - 使用 Ctrl+C 可以停止服务" -ForegroundColor Gray
Write-Host "  - 关闭 PowerShell 窗口也会停止对应服务" -ForegroundColor Gray
Write-Host "" 

# 尝试打开浏览器
try {
    Start-Process "http://localhost:5173"
    Write-Host "🌐 已在默认浏览器中打开前端界面" -ForegroundColor Green
} catch {
    Write-Host "⚠️  无法自动打开浏览器，请手动访问: http://localhost:5173" -ForegroundColor Yellow
}

Write-Host "" 
Write-Host "按任意键退出此脚本 (服务将继续在后台运行)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")