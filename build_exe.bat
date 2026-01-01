@echo off
echo ========================================
echo iOS Photo Mover - Build Executable
echo ========================================
echo.

echo [1/3] Installing PyInstaller...
pip install pyinstaller

echo.
echo [2/3] Building executable...
python -m PyInstaller --onefile --windowed --name "iOS-Photo-Mover" main.py

echo.
echo [3/3] Done!
echo.
echo Executable created in: dist\iOS-Photo-Mover.exe
echo.
pause

