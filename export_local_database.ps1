# Local Database Export Script for PowerShell
# यह script local database को export करेगा

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Local Database Export" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Exporting database to db_export.json..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

python manage.py dumpdata --exclude contenttypes --exclude auth.permission --exclude sessions --natural-foreign --natural-primary --indent 2 > db_export.json

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error during export!" -ForegroundColor Red
    pause
    exit 1
}

$fileSize = (Get-Item db_export.json).Length / 1MB

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Export Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "File created: db_export.json" -ForegroundColor Green
Write-Host "File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Git push (temporary): git add db_export.json && git commit -m 'temp: add db export' && git push"
Write-Host "2. Railway migrations: railway run python manage.py migrate"
Write-Host "3. Railway import: railway run python manage.py loaddata db_export.json"
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

