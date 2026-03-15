@echo off
cd /d %~dp0
set PATH=%~dp0toolkit\python311;%~dp0adb;%PATH%
python fgo_bot_auto_mas.py %*
