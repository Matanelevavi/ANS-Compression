@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: שלב 1: בניית המנוע (Compilation)
:: ==========================================
echo.
echo [1/2] Building HTSCodecs Engine...

:: קומפילציה של קבצי ה-C (הקבצים נמצאים בתיקייה הנוכחית)
gcc -c -O3 rANS_static.c pack.c utils.c
if %errorlevel% neq 0 goto error

:: קומפילציה של ה-Main וחיבור הכל
g++ -O3 -fpermissive main.cpp rANS_static.o pack.o utils.o -o htscodecs_ans.exe
if %errorlevel% neq 0 goto error

:: מחיקת קבצי זבל (.o) שנשארו
del *.o

echo Build Success! Engine is ready.
echo.

:: ==========================================
:: שלב 2: הרצת הבנצ'מארק (Benchmark)
:: ==========================================
echo [2/2] Starting Benchmark...

:: הגדרות נתיבים מעודכנות
set COMPRESSOR=htscodecs_ans.exe
set LOG_FILE=../../results/HTSCodecs_Results.csv
set TEST_DIR=../../corpus/cantrbry
set OUTPUT_EXTENSION=.hts

:: וודא שתיקיית התוצאות קיימת
if not exist "../../results" mkdir "../../results"

:: משתנים לסיכום
set TOTAL_ORIG=0
set TOTAL_COMP=0

:: איפוס וכתיבת כותרות לקובץ ה-CSV
if exist "%LOG_FILE%" del "%LOG_FILE%"
echo Filename,Original_Size,Compressed_Size,Ratio_Percent,Savings_Percent > "%LOG_FILE%"

:: לולאה ראשית על קבצי הקורפוס
for %%f in ("%TEST_DIR%\*") do (
    set INPUT_FILE=%%f
    set FILENAME_ONLY=%%~nxf
    set OUTPUT_FILE=!FILENAME_ONLY!%OUTPUT_EXTENSION%
    
    :: קבלת גודל מקורי בעזרת PowerShell
    set ORIGINAL_SIZE=0
    for /f "usebackq" %%s in (`powershell -Command "(Get-Item '%%f').Length"`) do set ORIGINAL_SIZE=%%s
    
    :: ביצוע דחיסה (מצב 'c' לפי ה-main.cpp)
    !COMPRESSOR! c "%%f" "!OUTPUT_FILE!" > NUL
    
    if exist "!OUTPUT_FILE!" (
        :: קבלת גודל דחוס
        set COMPRESSED_SIZE=0
        for /f "usebackq" %%c in (`powershell -Command "(Get-Item '!OUTPUT_FILE!').Length"`) do set COMPRESSED_SIZE=%%c
        
        :: חישוב אחוזים
        set RATIO=0
        set SAVINGS=0
        if !ORIGINAL_SIZE! GTR 0 (
            for /f "usebackq" %%s in (`powershell -Command "$s=100.0 - ([long]!COMPRESSED_SIZE!*100.0)/[long]!ORIGINAL_SIZE!; '{0:N2}' -f $s"`) do set SAVINGS=%%s
            for /f "usebackq" %%r in (`powershell -Command "$r=([long]!COMPRESSED_SIZE!*100.0)/[long]!ORIGINAL_SIZE!; '{0:N2}' -f $r"`) do set RATIO=%%r
        )

        :: סיכום כולל לסטטיסטיקה
        for /f "usebackq" %%t in (`powershell -Command "[long]!TOTAL_ORIG! + [long]!ORIGINAL_SIZE!"`) do set TOTAL_ORIG=%%t
        for /f "usebackq" %%t in (`powershell -Command "[long]!TOTAL_COMP! + [long]!COMPRESSED_SIZE!"`) do set TOTAL_COMP=%%t
        
        :: כתיבה ללוג (קובץ ה-CSV)
        echo !FILENAME_ONLY!,!ORIGINAL_SIZE!,!COMPRESSED_SIZE!,!RATIO!,!SAVINGS! >> "%LOG_FILE%"
        echo Processed: !FILENAME_ONLY! (Saved: !SAVINGS!%%)
        
        :: ניקוי הקובץ הדחוס הזמני
        del "!OUTPUT_FILE!"
    )
)

:: סיכום סופי לשורה האחרונה באקסל
set TOT_RATIO=0
set TOT_SAVINGS=0
if !TOTAL_ORIG! GTR 0 (
    for /f "usebackq" %%s in (`powershell -Command "$s=100.0 - ([long]!TOTAL_COMP!*100.0)/[long]!TOTAL_ORIG!; '{0:N2}' -f $s"`) do set TOT_SAVINGS=%%s
    for /f "usebackq" %%r in (`powershell -Command "$r=([long]!TOTAL_COMP!*100.0)/[long]!TOTAL_ORIG!; '{0:N2}' -f $r"`) do set TOT_RATIO=%%r
    
    echo ------------------------------------------ >> "%LOG_FILE%"
    echo TOTAL,!TOTAL_ORIG!,!TOTAL_COMP!,!TOT_RATIO!,!TOT_SAVINGS! >> "%LOG_FILE%"
)

echo.
echo Done. Results saved in: %LOG_FILE%
start "" "%LOG_FILE%"
exit /b

:error
echo.
echo !!! BUILD FAILED !!!
echo Please check the source code in "libs/htscodecs".
pause