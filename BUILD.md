# Building Executable

This guide explains how to build a standalone `.exe` file for distribution.

## Quick Build

### Option 1: Simple Build (Recommended for testing)

Run the simple build script:

```bash
build_exe.bat
```

This will create `dist\iOS-Photo-Mover.exe` (~15-20 MB)

### Option 2: Advanced Build (Recommended for distribution)

Run the advanced build script with optimizations:

```bash
build_advanced.bat
```

This will create an optimized `dist\iOS-Photo-Mover.exe` with all dependencies included.

## Manual Build

If you prefer to build manually:

1. **Install PyInstaller**:
```bash
pip install pyinstaller
```

2. **Build the executable**:
```bash
pyinstaller --onefile --windowed --name "iOS-Photo-Mover" main.py
```

3. **Find the executable**:
   - Location: `dist\iOS-Photo-Mover.exe`
   - Size: ~15-20 MB

## Build Options Explained

- `--onefile`: Bundle everything into a single .exe file
- `--windowed`: No console window (GUI only)
- `--name`: Name of the executable
- `--hidden-import`: Explicitly include modules that PyInstaller might miss
- `--add-data`: Include additional files (like README)

## Distribution

After building:

1. **Test the executable**:
   - Run `dist\iOS-Photo-Mover.exe`
   - Test all features
   - Check if all dependencies work

2. **Distribute**:
   - Share the `iOS-Photo-Mover.exe` file
   - Users do NOT need Python installed
   - Users still need iTunes or Apple Mobile Device Support

3. **Optional - Create installer**:
   - Use Inno Setup or NSIS to create an installer
   - Include README and LICENSE

## Troubleshooting

### Executable is too large
- Normal size is 15-20 MB due to Python runtime and dependencies
- This is expected for PyInstaller builds

### Missing modules error
- Add the missing module to `--hidden-import` in the build script
- Example: `--hidden-import module_name`

### Antivirus flags the .exe
- This is common with PyInstaller executables
- Sign the executable with a code signing certificate (optional)
- Users may need to add exception in their antivirus

### Application crashes on startup
- Test on a clean Windows machine without Python
- Check if iTunes/Apple Mobile Device Support is installed
- Review the error message in the console (use `--console` flag for debugging)

## System Requirements for Built Executable

Users need:
- Windows 10 or later
- iTunes or Apple Mobile Device Support
- USB cable for iOS device
- No Python installation required!

## File Size Comparison

- Source code: ~50 KB
- With dependencies: ~5 MB
- Built executable: ~15-20 MB
- This is normal for PyInstaller builds

## Notes

- The first run might be slower as Windows extracts the bundled files
- Subsequent runs will be faster
- The executable is portable - no installation needed
- Configuration is saved in `config.json` next to the executable

