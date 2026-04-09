@echo off
chcp 65001 >nul
title AI 英语演讲视频生成系统
echo ====================================
echo AI 英语演讲视频生成系统
echo ====================================
echo.

:: 使用虚拟环境 Python 运行主程序
"D:\_BiShe\env\Scripts\python.exe" "%~dp0main.py" %*

pause
