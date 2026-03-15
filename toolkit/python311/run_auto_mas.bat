@echo off
chcp 936 >nul
title FGO Bot - AUTO-MAS

set _root=%~dp0
set _root=%_root:~0,-1%
%~d0
cd %_root%

set _pyBin=%_root%\toolkit\python311
set _adbBin=%_root%\adb
set PATH=%_pyBin%;%_pyBin%\Scripts;%_adbBin%;%PATH%

python fgo_bot_auto_mas.py %*
