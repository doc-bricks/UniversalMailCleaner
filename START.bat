@echo off
setlocal
cd /d "%~dp0"

if exist "dist\UniversalMailCleaner\UniversalMailCleaner.exe" (
    echo Starte UniversalMailCleaner EXE...
    start "" "dist\UniversalMailCleaner\UniversalMailCleaner.exe"
    exit /b 0
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    pause
    exit /b 1
)
echo Starte UniversalMailCleaner per Python...
python "mail_imap_cleaner_v1.py"
if errorlevel 1 pause
