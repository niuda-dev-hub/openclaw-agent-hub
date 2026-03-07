# OpenClaw Agent Hub 统一启动脚本
# 用法: powershell -ExecutionPolicy Bypass -File start.ps1

function Show-Menu {
    Clear-Host
    Write-Host "============================" -ForegroundColor Cyan
    Write-Host "   OpenClaw Agent Hub 启动器" -ForegroundColor Cyan
    Write-Host "============================" -ForegroundColor Cyan
    Write-Host "1) 🚀 同时启动前后端 (推荐)"
    Write-Host "2) ⚡ 仅运行后端 (FastAPI/Uvicorn)"
    Write-Host "3) 🎨 仅运行前端 (React/Vite)"
    Write-Host "q) 退出"
    Write-Host "----------------------------"
}

function Start-Backend {
    Write-Host "正在启动后端服务 (localhost:8000)..." -ForegroundColor Green
    Set-Location "$PSScriptRoot/src"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn agent_hub.main:app --host 127.0.0.1 --port 8000 --reload"
}

function Start-Frontend {
    Write-Host "正在启动前端开发模式 (localhost:5173)..." -ForegroundColor Green
    Set-Location "$PSScriptRoot/frontend"
    if (Test-Path ".env") {
        Write-Host "检测到 .env 配置文件" -ForegroundColor Gray
    }
    else {
        Write-Host "未检测到 .env，正在使用默认配置并创建预览..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
    }
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"
}

do {
    Show-Menu
    $choice = Read-Host "请选择操作 [1-3, q]"
    
    switch ($choice) {
        '1' {
            Start-Backend
            Start-Frontend
            Write-Host "服务均已启动。请在弹出的新窗口中查看日志。" -ForegroundColor Cyan
            exit
        }
        '2' {
            Start-Backend
            exit
        }
        '3' {
            Start-Frontend
            exit
        }
        'q' {
            exit
        }
        default {
            Write-Host "无效选项，请重新选择" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
} while ($true)
