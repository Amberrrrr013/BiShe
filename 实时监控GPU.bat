@echo off
chcp 65001 >nul
title SadTalker GPU 实时监控

echo ========================================
echo   SadTalker GPU 实时监控
echo   每 2 秒刷新一次
echo   按 Ctrl+C 停止
echo ========================================
echo.

:loop
cls
echo [%date% %time%]
echo ------------ GPU 状态 ------------
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader 2>nul
echo.

echo ------------ Python 进程 ------------
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /i "python" || echo 无Python进程
echo.

echo ------------ SadTalker 进程 ------------
wmic process where "commandline like '%%inference%%'" get commandline,processid 2>nul || echo 无SadTalker进程
echo.

echo ------------ GPU 利用率详情 ------------
nvidia-smi --query-gpu=utilization.gpu,utilization.memory --format=csv,noheader 2>nul
echo.

echo =======================================
echo 等待 2 秒后刷新...
timeout /t 2 /nobreak >nul
goto loop
