@echo off
chcp 65001 >nul
title AI 英语演讲视频生成系统
cd /d "%~dp0"

:: 使用虚拟环境 Python 启动 GUI
"D:\_BiShe\env\Scripts\python.exe" gui_app.py
pause
