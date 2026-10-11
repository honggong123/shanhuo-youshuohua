@echo off
powershell -NoProfile -Command "Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath('Startup')) '山货有话说.lnk') -ErrorAction SilentlyContinue"
echo 已取消开机自启。如原本未设置过，则没有任何变化。
pause
