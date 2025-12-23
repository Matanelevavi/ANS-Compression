@echo off
echo Building Arithmetic Reference Engines...

:: בניית הגרסה הסטנדרטית (N)
cd reference_arith
gcc -O3 arith_n.c bitio.c errhand.c main-c.c -o arith_n.exe
cd ..

:: בניית הגרסה הפשוטה (Simple)
cd reference_arith_simple
gcc -O3 arith.c bitio.c errhand.c main-c.c -o arith_simple.exe
cd ..

echo Done! Executables created in subfolders.
pause