@echo off
cd /d "%~dp0"
if not exist .venv call setup.bat
call .venv\Scripts\activate
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name MediaHub --collect-all imageio_ffmpeg --collect-all deno --collect-submodules yt_dlp app.py
echo.
echo Creando acceso directo en el escritorio...
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\MediaHub.lnk'); $s.TargetPath='%~dp0dist\MediaHub\MediaHub.exe'; $s.WorkingDirectory='%~dp0dist\MediaHub'; $s.Save()"
echo.
echo Listo: dist\MediaHub\MediaHub.exe
pause
