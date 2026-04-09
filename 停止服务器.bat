@echo off
chcp 65001 >nul
title 停止服务器

echo 正在停止 Flask 服务器...

taskkill /f /im python.exe 2>nul
taskkill /f /im pythonw.exe 2>nul

echo 服务器已停止
timeout /t 2 >nul
