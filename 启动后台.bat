@echo off
title 山货有话说 - 后台服务
cd /d "%~dp0backend"

rem ---- 已在运行则静默退出（开机自启时不重复起服务）----
powershell -NoProfile -Command "try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',8000);$c.Close();exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel%==0 exit /b 0

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
