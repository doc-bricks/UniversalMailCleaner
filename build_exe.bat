@echo off
setlocal
cd /d "%~dp0"

set "BUILD_ROOT=C:\_Local_DEV\codex_build\universalmailcleaner"
set "DIST_PATH=%CD%\dist"
set "SPEC_PATH=%CD%\UniversalMailCleaner.spec"

if exist "%BUILD_ROOT%" rmdir /s /q "%BUILD_ROOT%"
mkdir "%BUILD_ROOT%" >nul 2>&1

python -m PyInstaller --noconfirm --clean --workpath "%BUILD_ROOT%\work" --distpath "%DIST_PATH%" "%SPEC_PATH%"
if errorlevel 1 (
    echo [FEHLER] PyInstaller-Build fehlgeschlagen.
    pause
    exit /b 1
)

echo [OK] dist\UniversalMailCleaner\UniversalMailCleaner.exe aktualisiert.
