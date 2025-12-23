@echo off
setlocal enabledelayedexpansion

:: ------------------------------------------
:: 1. הגדרות נתיבים מעודכנות למבנה החדש
:: ------------------------------------------
set COMPRESSOR=compressor.exe
:: שמירת התוצאות בתיקיית ה-results המרכזית
set LOG_FILE=../../results/Rygrans_Results.csv
:: הצבעה לתיקיית הקורפוס החדשה
set TEST_DIR=../../corpus/cantrbry
set OUTPUT_EXTENSION=.rans

:: יצירת שם ייחודי לתיקיית ריצה
for /f "usebackq tokens=*" %%a in (`powershell -Command "Get-Date -format 'yyyy-MM-dd_HH-mm-ss'"`) do set TIMESTAMP=%%a
set OUTPUT_DIR=Run_!TIMESTAMP!

if not exist "../../results" mkdir "../../results"
mkdir "!OUTPUT_DIR!"

:: ------------------------------------------
:: 2. איפוס וכתיבת כותרות לקובץ ה-Excel (CSV)
:: ------------------------------------------
if exist "%LOG_FILE%" del "%LOG_FILE%"
echo Filename,Original_Size,Compressed_Size,Ratio_Percent,Savings_Percent > "%LOG_FILE%"

echo Starting Rygrans Benchmark...
echo Input Folder: %TEST_DIR%
echo.

:: ------------------------------------------
:: 3. לולאת הרצה על קבצי הקורפוס
:: ------------------------------------------
for %%f in ("%TEST_DIR%\*") do (
    set INPUT_FILE=%%f
    set FILENAME_ONLY=%%~nxf
    
    set OUTPUT_FILE=!OUTPUT_DIR!\!FILENAME_ONLY!%OUTPUT_EXTENSION%
    
    :: קבלת גודל מקורי
    set ORIGINAL_SIZE=0
    for /f "usebackq" %%s in (`powershell -Command "(Get-Item '%%f').Length"`) do set ORIGINAL_SIZE=%%s
    
    :: ביצוע דחיסה
    !COMPRESSOR! c "%%f" "!OUTPUT_FILE!" > NUL
    
    if exist "!OUTPUT_FILE!" (
        :: קבלת גודל דחוס
        set COMPRESSED_SIZE=0
        for /f "usebackq" %%c in (`powershell -Command "(Get-Item '!OUTPUT_FILE!').Length"`) do set COMPRESSED_SIZE=%%c
        
        :: חישוב אחוזים בעזרת PowerShell
        set RATIO=0
        set SAVINGS=0
        if !ORIGINAL_SIZE! GTR 0 (
            for /f "usebackq" %%s in (`powershell -Command "$s=100.0 - ([long]!COMPRESSED_SIZE!*100.0)/[long]!ORIGINAL_SIZE!; '{0:N2}' -f $s"`) do set SAVINGS=%%s
            for /f "usebackq" %%r in (`powershell -Command "$r=([long]!COMPRESSED_SIZE!*100.0)/[long]!ORIGINAL_SIZE!; '{0:N2}' -f $r"`) do set RATIO=%%r
        )
        
        :: כתיבה לקובץ ה-CSV
        echo !FILENAME_ONLY!,!ORIGINAL_SIZE!,!COMPRESSED_SIZE!,!RATIO!,!SAVINGS! >> "%LOG_FILE%"
        echo Processed: !FILENAME_ONLY!
    )
)

echo.
echo Benchmark Complete. Results saved in: %LOG_FILE%
start "" %LOG_FILE%
endlocal