@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
echo Installing Antigravity Pure HUD...
call agy plugin install "%SCRIPT_DIR:~0,-1%"
echo Done! In AGY CLI, enable statusline with:
echo /statusline %SCRIPT_DIR%hooks\status-line.bat
