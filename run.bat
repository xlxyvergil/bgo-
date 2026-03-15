@echo off
chcp 936 >nul
title FGO Bot

set "_root=%~dp0"
set "_root=%_root:~0,-1%"
%~d0
cd "%_root%"

set "_pyBin=%_root%\toolkit\python311"
set "_adbBin=%_root%\adb"
set "PATH=%_pyBin%;%_pyBin%\Scripts;%_adbBin%;%PATH%"

echo ==========================================
echo           FGO Automation Script
echo ==========================================
echo.
echo [INFO] Using embedded Python: %_pyBin%\python.exe
echo [INFO] Using ADB: %_adbBin%\adb.exe
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Embedded Python not found. Please check toolkit\python311 directory.
    pause
    exit /b 1
)

echo Starting automation...
echo.
python fgo_bot.py

echo.
echo ==========================================
echo Script finished
echo.
