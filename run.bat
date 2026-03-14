@echo off
chcp 936 >nul
title FGO Bot

echo ==========================================
echo           FGO Automation Script
echo ==========================================
echo.

py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.6+
    pause
    exit /b 1
)

echo Starting automation...
echo.
cd /d "%~dp0"
py fgo_bot.py

echo.
echo ==========================================
echo Script finished
echo.
pause
