@echo off
chcp 65001 >nul
title AI 英语演讲视频生成系统 - 交互式控制台

echo ========================================
echo   AI 英语演讲视频生成系统 - 交互式服务器
echo ========================================
echo.
echo 功能说明:
echo   - 在此窗口输入命令查看任务进度
echo   - 输入 help 查看可用命令
echo   - 输入 exit 或 Ctrl+C 退出
echo.

cd /d "%~dp0"

echo [1/4] 检查虚拟环境...
if not exist "D:\_BiShe\env\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在: D:\_BiShe\env\Scripts\python.exe
    pause
    exit /b 1
)

echo [2/4] 检查依赖...
"D:\_BiShe\env\Scripts\python.exe" -c "import flask, langgraph" 2>nul
if errorlevel 1 (
    echo [错误] 缺少依赖，请运行: D:\_BiShe\env\Scripts\pip.exe install flask langgraph
    pause
    exit /b 1
)

echo [3/4] 检查端口...
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo [警告] 端口 5000 已被占用！
    echo 请先关闭其他服务器实例
    pause
    exit /b 1
)

echo [4/4] 启动交互式服务器...
echo.
echo ========================================
echo   启动完成，输入 help 查看可用命令
echo ========================================
echo.

"D:\_BiShe\env\Scripts\python.exe" server_interactive.py

pause
