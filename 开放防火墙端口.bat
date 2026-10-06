@echo off
chcp 65001 >nul
title 开放防火墙 8000 端口（真机预览用）
netsh advfirewall firewall add rule name="Shanhuo8000" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1
if %errorlevel%==0 goto ok
echo 需要管理员权限，正在请求提权……请在弹窗中点"是"
powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
exit /b
:ok
echo ================================================
echo   端口 8000 已在防火墙放行，真机预览的网络准备完成
echo ================================================
pause
