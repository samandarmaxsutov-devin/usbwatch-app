@echo off
rem Install USBWatch for the current user: copy the exe, create Desktop + Start Menu
rem shortcuts, and register it in "Installed apps". Run AFTER build.bat. No admin needed.
setlocal
cd /d "%~dp0"

if not exist "dist\USBWatch.exe" (
  echo dist\USBWatch.exe topilmadi. Avval build.bat ni ishga tushiring.
  exit /b 1
)

set "APPDIR=%LOCALAPPDATA%\Programs\USBWatch"
set "EXE=%APPDIR%\USBWatch.exe"
set "ICO=%APPDIR%\usbwatch.ico"
set "SM=%APPDATA%\Microsoft\Windows\Start Menu\Programs\USBWatch.lnk"
set "DT=%USERPROFILE%\Desktop\USBWatch.lnk"

echo === Fayllarni ko'chirish: %APPDIR% ===
if not exist "%APPDIR%" mkdir "%APPDIR%"
copy /y "dist\USBWatch.exe" "%EXE%" >nul
if exist "assets\usbwatch.ico" copy /y "assets\usbwatch.ico" "%ICO%" >nul
copy /y "uninstall.bat" "%APPDIR%\uninstall.bat" >nul

echo === Yorliqlar (Desktop + Start Menu) ===
powershell -NoProfile -Command ^
  "$w=New-Object -ComObject WScript.Shell;" ^
  "foreach($p in @('%DT%','%SM%')){ $s=$w.CreateShortcut($p); $s.TargetPath='%EXE%';" ^
  " $s.IconLocation='%ICO%'; $s.WorkingDirectory='%APPDIR%'; $s.Description='USBWatch'; $s.Save() }"

echo === "O'rnatilgan ilovalar" ro'yxatiga qo'shish ===
set "KEY=HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\USBWatch"
reg add "%KEY%" /v DisplayName /t REG_SZ /d "USBWatch" /f >nul
reg add "%KEY%" /v DisplayIcon /t REG_SZ /d "%ICO%" /f >nul
reg add "%KEY%" /v DisplayVersion /t REG_SZ /d "2.0.0" /f >nul
reg add "%KEY%" /v Publisher /t REG_SZ /d "USBWatch" /f >nul
reg add "%KEY%" /v InstallLocation /t REG_SZ /d "%APPDIR%" /f >nul
reg add "%KEY%" /v UninstallString /t REG_SZ /d "\"%APPDIR%\uninstall.bat\"" /f >nul
reg add "%KEY%" /v NoModify /t REG_DWORD /d 1 /f >nul
reg add "%KEY%" /v NoRepair /t REG_DWORD /d 1 /f >nul

echo.
echo DONE: USBWatch o'rnatildi.
echo  - Desktop yorlig'i: %DT%
echo  - Start menyu: USBWatch
echo  - Sozlamalar ^> Ilovalar ^> O'rnatilgan ilovalar ^> USBWatch
endlocal
