@echo off
chcp 65001 >nul
title SadTalker GPU 监控

echo ========================================
echo   SadTalker GPU 进度监控
echo   按 Ctrl+C 停止监控
echo ========================================
echo.

:loop
echo [%date% %time%] GPU状态:
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv

echo.
echo [%date% %time%] Python 进程:
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /i "python"

echo.
echo [%date% %time%] SadTalker 相关进程:
wmic process where "commandline like '%%sadtalker%%' or commandline like '%%inference%%'" get commandline,processid 2>nul

echo.
echo ----------------------------------------
echo 等待 3 秒后刷新...
timeout /t 3 /nobreak >nul
cls
goto loop
