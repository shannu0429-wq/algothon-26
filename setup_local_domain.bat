@echo off
set "HOSTS_PATH=%WINDIR%\System32\drivers\etc\hosts"
findstr /i "jobalign-ai.com" "%HOSTS_PATH%" >nul 2>&1
if %errorlevel% neq 0 (
    echo 127.0.0.1 jobalign-ai.com>>"%HOSTS_PATH%"
    echo 127.0.0.1 www.jobalign-ai.com>>"%HOSTS_PATH%"
    ipconfig /flushdns >nul
    echo domain mapped successfully: http://jobalign-ai.com:5000
) else (
    echo domain jobalign-ai.com is already mapped in hosts file
)
pause
