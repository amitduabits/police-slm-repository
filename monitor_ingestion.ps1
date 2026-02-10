# Monitor PDF Archive Ingestion Progress
# Run this script to see live progress

$LOG_DIR = "logs"
$TASK_OUTPUT = "C:\Users\Lenovo\AppData\Local\Temp\claude\d--projects-Ongoing-gujarat-police-Implementation-project-gujpol-slm-complete-gujpol-slm-complete\tasks\b65443d.output"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "PDF Archive Ingestion Monitor" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if task output exists
if (Test-Path $TASK_OUTPUT) {
    Write-Host "Reading from task output..." -ForegroundColor Green
    Get-Content $TASK_OUTPUT -Tail 50 -Wait
} else {
    Write-Host "Task output not found. Checking logs directory..." -ForegroundColor Yellow

    # Find the latest log file
    $latestLog = Get-ChildItem -Path $LOG_DIR -Filter "pdf_ingestion_*.log" -ErrorAction SilentlyContinue |
                 Sort-Object LastWriteTime -Descending |
                 Select-Object -First 1

    if ($latestLog) {
        Write-Host "Following log file: $($latestLog.FullName)" -ForegroundColor Green
        Get-Content $latestLog.FullName -Tail 50 -Wait
    } else {
        Write-Host "No log files found. Process may not have started yet." -ForegroundColor Red
        Write-Host ""
        Write-Host "To start ingestion manually:" -ForegroundColor Yellow
        Write-Host "  python -m src.ingestion.pdf_archive_ingest" -ForegroundColor White
    }
}
