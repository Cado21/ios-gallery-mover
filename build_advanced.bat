@echo off
echo ========================================
echo iOS Photo Mover - Advanced Build
echo ========================================
echo.

echo [1/4] Installing PyInstaller...
pip install pyinstaller

echo.
echo [2/4] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo [3/4] Building executable with optimizations...
python -m PyInstaller --clean --noconfirm ^
    --onefile ^
    --windowed ^
    --name "iOS-Photo-Mover" ^
    --add-data "README.md;." ^
    --hidden-import win32com.client ^
    --hidden-import win32file ^
    --hidden-import pywintypes ^
    --hidden-import pythoncom ^
    --hidden-import hachoir.parser ^
    --hidden-import hachoir.metadata ^
    main.py

echo.
echo [4/4] Cleaning up...
rmdir /s /q build
del /q *.spec

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable location: dist\iOS-Photo-Mover.exe
echo.
echo You can now distribute this .exe file to users.
echo Users do NOT need Python installed!
echo.
pause

