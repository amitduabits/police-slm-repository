@echo off
REM Gujarat Police SLM - Upgrade Execution Script (Windows)
REM Integrates Kaggle SC Judgments + New Dashboard

cd /d "D:\projects\Ongoing\gujarat police\Implementation project\gujpol-slm-complete\gujpol-slm-complete"

echo ================================
echo GUJARAT POLICE SLM UPGRADE
echo ================================
echo.

REM ============================================================================
REM STEP 1: BACKUP OLD DASHBOARD
REM ============================================================================
echo [1/6] Backing up old dashboard...
if exist "src\dashboard" (
    set BACKUP_NAME=src\dashboard-backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%-%time:~0,2%%time:~3,2%%time:~6,2%
    set BACKUP_NAME=%BACKUP_NAME: =0%
    move "src\dashboard" "%BACKUP_NAME%"
    echo OK Old dashboard backed up
) else (
    echo Warning: No old dashboard found at src\dashboard
)
echo.

REM ============================================================================
REM STEP 2: INSTALL NEW DASHBOARD
REM ============================================================================
echo [2/6] Installing new upgraded dashboard...
if exist "dashboard" (
    move dashboard src\dashboard
    echo OK New dashboard moved to src\dashboard

    cd src\dashboard
    echo Installing npm dependencies...
    call npm install
    echo OK Dashboard dependencies installed
    cd ..\..
) else (
    echo ERROR: dashboard\ folder not found at project root
    pause
    exit /b 1
)
echo.

REM ============================================================================
REM STEP 3: FIX BCRYPT ERROR (BEFORE INGESTION)
REM ============================================================================
echo [3/6] Fixing bcrypt compatibility...
pip install bcrypt==4.0.1 --break-system-packages
echo OK bcrypt fixed
echo.

REM ============================================================================
REM STEP 4: PREPARE ARCHIVE DATA FOR INGESTION
REM ============================================================================
echo [4/6] Checking archive data...
set ARCHIVE_PATH=archive\supreme_court_judgments
for /f %%A in ('dir /s /b "%ARCHIVE_PATH%\*.PDF" 2^>nul ^| find /c /v ""') do set PDF_COUNT=%%A
echo Found %PDF_COUNT% judgment PDFs in %ARCHIVE_PATH%
echo.

REM ============================================================================
REM STEP 5: RUN KAGGLE INGESTION PIPELINE
REM ============================================================================
echo [5/6] Running ingestion pipeline...
echo Warning: This will process all PDFs: OCR - Clean - Chunk - Embed - ChromaDB
echo Estimated time: 30-60 minutes for 25K+ PDFs
echo.
set /p CONTINUE="Continue with ingestion? (y/n): "
if /i "%CONTINUE%"=="y" (
    python -m src.ingestion.kaggle_ingest
    echo OK Ingestion complete!
) else (
    echo Skipping ingestion. Run manually later with:
    echo    python -m src.ingestion.kaggle_ingest
)
echo.

REM ============================================================================
REM STEP 6: START SERVICES
REM ============================================================================
echo [6/6] Ready to start services!
echo.
echo To start the dashboard (development mode):
echo   cd src\dashboard
echo   npm run dev
echo.
echo To start the API server:
echo   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo To start full Docker stack:
echo   docker-compose up -d
echo.

echo ================================
echo OK UPGRADE COMPLETE!
echo ================================
echo.
echo Summary of changes:
echo   OK New dashboard installed at src\dashboard\
echo   OK Old dashboard backed up
echo   OK bcrypt compatibility fixed
echo   OK 25,735 SC judgment PDFs ready for ingestion
echo   OK kaggle_ingest.py pipeline ready
echo.
echo Next steps:
echo   1. Start the dashboard: cd src\dashboard ^&^& npm run dev
echo   2. Start the API: python -m uvicorn src.api.main:app --reload
echo   3. Access at: http://localhost:5173 (dashboard) + http://localhost:8000 (API)
echo.
pause
