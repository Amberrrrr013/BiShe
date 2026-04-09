@echo off
chcp 65001 >nul
title SadTalker GPU 详细监控

echo ========================================
echo   SadTalker GPU 详细监控
echo   每 3 秒刷新一次
echo   按 Ctrl+C 停止
echo ========================================
echo.

:loop
cls
echo [%date% %time%]
echo ============ GPU 核心温度 ============
nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader 2>nul

echo ============ GPU 利用率 ============
nvidia-smi --query-gpu=utilization.gpu,utilization.memory --format=csv,noheader 2>nul

echo ============ GPU 显存使用 ============
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>nul

echo ============ 显存使用详情 ============
nvidia-smi --query-compute-apps=pid,used_memory --format=csv 2>nul

echo ============ Python 进程 ============
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /i "python" || echo 无Python进程

echo.
echo =======================================
timeout /t 3 /nobreak >nul
goto loop
