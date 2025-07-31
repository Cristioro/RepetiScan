@echo off
setlocal

set SCRIPT=repetiscan.py
set EXENAME=RepetiScan Music
set ICON=icono.ico
set DISTFOLDER=dist
set OUTPUT=%DISTFOLDER%\%EXENAME%.exe

echo 🛠️ Compilador de RepetiScan Music

REM Verificar existencia del script
if not exist "%SCRIPT%" (
    echo ❌ No se encontró "%SCRIPT%"
    pause
    exit /b
)

REM Verificar existencia del icono
if not exist "%ICON%" (
    echo ❌ No se encontró "%ICON%"
    pause
    exit /b
)

REM Verificar si ya existe compilación anterior
if exist "%OUTPUT%" (
    echo ⚠️ Ya existe una compilación previa: "%OUTPUT%"
    choice /M "¿Deseas eliminarla antes de continuar?"
    if errorlevel 2 (
        echo ❌ Cancelado por el usuario.
        pause
        exit /b
    )
    echo 🔥 Borrando compilación anterior...
    rmdir /S /Q build
    rmdir /S /Q dist
    del /Q "%EXENAME%.spec"
)

echo 🔧 Compilando %SCRIPT% a .exe...
pyinstaller --name "%EXENAME%" --onefile --windowed --icon="%ICON%" "%SCRIPT%"

echo ✅ Compilación completada. Ejecutable generado en: "%OUTPUT%"
pause
