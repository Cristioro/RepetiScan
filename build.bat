@echo off
setlocal

echo This script will delete the dist and build folders and the RepetiScan Music.spec file if they exist.
set /p CONFIRM="Do you want to continue? (y/n): "
if /I not "%CONFIRM%"=="y" (
    echo Operation canceled.
    exit /b
)

REM Remove previous folders and file if they exist
if exist dist (
    rmdir /s /q dist
    echo Folder 'dist' deleted.
)
if exist build (
    rmdir /s /q build
    echo Folder 'build' deleted.
)
if exist "RepetiScan Music.spec" (
    del "RepetiScan Music.spec"
    echo File 'RepetiScan Music.spec' deleted.
)

REM Ejecutar PyInstaller
if not exist "assets\icon.ico" (
    echo 'assets\icon.ico' was not found. Make sure the file exists.
    pause
    exit /b
)
if not exist main.py (
    echo 'main.py' was not found. Make sure the file exists.
    pause
    exit /b
)
if not exist lang.json (
    echo 'lang.json' was not found. Make sure the file exists.
    pause
    exit /b
)


echo Compiling repetiscan to executable...
pyinstaller --noconfirm --onefile --windowed --add-data "lang.json;." --icon "assets/icon.ico" --name "RepetiScan Music" main.py

echo.
echo Compilation finished.
pause