@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%..\release\OrdoCor.exe"

if exist "%EXE_PATH%" (
    start "" "%EXE_PATH%"
    exit /b 0
)

echo OrdoCor.exe was not found at:
echo %EXE_PATH%
echo.
echo Build the executable first, or edit this script to point to your installed OrdoCor.exe.
exit /b 1
