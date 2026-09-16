@echo off
title yeblock
cd /d "%~dp0"
:loop
node --max-old-space-size=8192 main.js
echo.
echo Tool da thoat (ma loi: %errorlevel%). Tu khoi dong lai sau 10 giay... (Ctrl+C de dung han)
timeout /t 10
goto loop
