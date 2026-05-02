@echo off
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    pause
    exit /b 1
)
echo Starte UniversalMailCleaner...
python "mail_imap_cleaner_v1.py"
if errorlevel 1 pause
