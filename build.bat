@echo off
echo === Building Project Saruman ===
uv run pyinstaller ProjectSaruman.spec --clean --noconfirm
if errorlevel 1 (
    echo BUILD FAILED
    pause
    exit /b 1
)

echo === Clearing local high scores for clean test run ===
for /f "tokens=*" %%i in ('powershell -Command "[System.Environment]::GetFolderPath(\"LocalApplicationData\")"') do set LOCALAPPDATA_PATH=%%i
del /f /q "%LOCALAPPDATA_PATH%\ProjectSaruman\ProjectSaruman\highscores.json" 2>nul
echo (done)

echo === Creating zip ===
powershell -Command "Compress-Archive -Path dist\ProjectSaruman -DestinationPath dist\ProjectSaruman-windows.zip -Force"
if errorlevel 1 (
    echo ZIP FAILED
    pause
    exit /b 1
)

echo.
echo === Done ===
echo Executable : dist\ProjectSaruman\ProjectSaruman.exe
echo Upload zip : dist\ProjectSaruman-windows.zip
echo.
pause
