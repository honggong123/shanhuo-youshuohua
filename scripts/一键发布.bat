@echo off
chcp 65001 >nul
title Shanhuo - Release (sync submission zip + cloud zip)
cd /d "%~dp0.."
python scripts\release.py %*
echo.
pause
