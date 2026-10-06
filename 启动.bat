@echo off
title 山货有话说 - 服务启动
cd /d "%~dp0backend"

rem ---- 已在运行则直接打开页面 ----
powershell -NoProfile -Command "try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',8000);$c.Close();exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel%==0 (
    echo 检测到服务已在运行，直接为你打开页面...
    start "" http://127.0.0.1:8000
    timeout /t 3 /nobreak >nul
    exit /b 0
)

echo ================================================
echo   《山货有话说》正在启动，请勿关闭本窗口
echo   关闭服务：直接关闭本窗口或按 Ctrl+C
echo ================================================

rem ---- 寻找 Python ----
where python >nul 2>&1
if %errorlevel%==0 (
    set "PYCMD=python"
    goto run
)
where py >nul 2>&1
if %errorlevel%==0 (
    set "PYCMD=py -3"
    goto run
)
echo [错误] 找不到 Python。请安装 Python 3 并勾选 "Add Python to PATH"，然后重试。
pause
exit /b 1

:run
start "" http://127.0.0.1:8000
%PYCMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo.
echo 服务已停止。如上方有报错信息，请把截图发给我。
pause
