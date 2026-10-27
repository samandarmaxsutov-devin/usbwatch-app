@echo off
rem Remove USBWatch for the current user: shortcuts, registry entry, autostart task and files.
setlocal
set "APPDIR=%LOCALAPPDATA%\Programs\USBWatch"
set "SM=%APPDATA%\Microsoft\Windows\Start Menu\Programs\USBWatch.lnk"
set "DT=%USERPROFILE%\Desktop\USBWatch.lnk"

echo === Yorliqlarni o'chirish ===
if exist "%DT%" del /q "%DT%"
if exist "%SM%" del /q "%SM%"

echo === Ro'yxatdan olib tashlash ===
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\USBWatch" /f >nul 2>nul
schtasks /Delete /TN USBWatch /f >nul 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v USBWatch /f >nul 2>nul

echo === Fayllarni o'chirish ===
rem Remove the install folder after this script exits (can't delete itself while running).
start "" cmd /c "timeout /t 2 >nul & rmdir /s /q ""%APPDIR%"""

echo.
echo USBWatch o'chirildi.
echo Eslatma: ma'lumotlar (C:\ProgramData\USBWatch) saqlanib qoldi. O'chirish uchun:
echo   rmdir /s /q "C:\ProgramData\USBWatch"
endlocal
