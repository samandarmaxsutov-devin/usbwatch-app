@echo off
rem Build a single-file USBWatch.exe with PyInstaller.
cd /d "%~dp0"

set PY=py
%PY% -V >nul 2>nul || set PY=python

echo === Installing dependencies ===
%PY% -m pip install -r requirements.txt pyinstaller || goto :fail

echo === Generating icon ===
%PY% -m usbwatch.views.appicon "assets\usbwatch.ico" || goto :fail

echo === Building USBWatch.exe ===
%PY% -m PyInstaller --noconfirm --onefile --windowed --name USBWatch ^
    --icon "assets\usbwatch.ico" ^
    --collect-all customtkinter ^
    --collect-submodules infi.systray ^
    run.py || goto :fail

echo.
echo DONE: dist\USBWatch.exe
echo Desktop + Start Menu yorliqlari uchun: install.bat
goto :eof

:fail
echo.
echo Build failed.
exit /b 1
