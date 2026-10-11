@echo off
cd /d "%~dp0"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $lnk = Join-Path ([Environment]::GetFolderPath('Startup')) '山货有话说.lnk'; $s = $ws.CreateShortcut($lnk); $s.TargetPath = '%~dp0启动后台.bat'; $s.WorkingDirectory = '%~dp0'; $s.WindowStyle = 7; $s.Save()"

if %errorlevel%==0 (
    echo ================================================
    echo   已开启开机自启！
    echo   以后每次开机将自动在后台运行服务，
    echo   直接打开 http://127.0.0.1:8000 即可使用。
    echo   如需取消，双击 取消开机自启.bat
    echo ================================================
) else (
    echo [错误] 设置失败，请把窗口截图发给我。
)
pause
