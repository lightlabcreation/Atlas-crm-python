@echo off
REM Local Database Export Script for Windows
REM यह script local database को export करेगा

echo ========================================
echo Local Database Export
echo ========================================
echo.

echo Exporting database to db_export.json...
echo This may take a few minutes...
echo.

python manage.py dumpdata --exclude contenttypes --exclude auth.permission --exclude sessions --natural-foreign --natural-primary --indent 2 > db_export.json

if errorlevel 1 (
    echo.
    echo Error during export!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Export Complete!
echo ========================================
echo.
echo File created: db_export.json
echo.
echo Next steps:
echo 1. Check file size: dir db_export.json
echo 2. Git push (temporary): git add db_export.json ^&^& git commit -m "temp: add db export" ^&^& git push
echo 3. Railway migrations: railway run python manage.py migrate
echo 4. Railway import: railway run python manage.py loaddata db_export.json
echo.
pause

