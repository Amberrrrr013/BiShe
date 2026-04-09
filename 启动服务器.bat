@echo off
chcp 65001 >nul
title AI 英语演讲视频生成系统

echo ========================================
echo   AI 英语演讲视频生成系统 - 服务器启动
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] 使用虚拟环境 Python

echo [1/3] 检查虚拟环境...
if not exist "D:\_BiShe\env\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在: D:\_BiShe\env\Scripts\python.exe
    pause
    exit /b 1
)

echo [2/3] 检查依赖...
"D:\_BiShe\env\Scripts\python.exe" -c "import flask, langgraph" 2>nul
if errorlevel 1 (
    echo [错误] 缺少依赖，请运行: D:\_BiShe\env\Scripts\pip.exe install flask langgraph
    pause
    exit /b 1
)

echo [3/3] 启动 Flask 服务器...
echo.
echo 服务器地址: http://127.0.0.1:5000
echo 按 Ctrl+C 停止服务器
echo.

"D:\_BiShe\env\Scripts\python.exe" server.py

pause
echo 前端界面:   http://127.0.0.1:5000/frontend
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

"C:\Users\ASUS\AppData\Local\Programs\Python\Python314\python.exe" server.py

pause
