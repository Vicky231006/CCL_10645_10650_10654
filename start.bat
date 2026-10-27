@echo off
REM Resumo launcher - double-click friendly. For options use start.ps1 directly.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
if errorlevel 1 pause
