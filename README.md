# iOS Photo Mover

A Windows application to transfer and organize photos from iOS devices to Windows PC via USB cable.

## Features

1. **iOS to PC Connection**: Connect to iOS devices via USB cable
2. **Photo Selection**: Easily select photos to transfer with checkboxes
3. **Sorting Options**: 
   - **Month_Year**: Sort by Month-Year (example: `2024-01`)
   - **Date_Month_Year**: Sort by Date-Month-Year (example: `2024-01-15`)
4. **Duplicate Handling**:
   - **overwrite**: Replace existing files
   - **keep_both**: Rename new files (e.g., `file_1.mov`)
   - **skip**: Skip files that already exist
5. **Unknown Folder**: Photos without dates will be moved to a configurable "Unknown" folder
6. **Configurable Paths**: Choose output location and Unknown folder as needed
7. **Metadata Preservation**: Maintains original file creation and modification dates
8. **Progress Tracking**: Real-time progress with remaining file count
9. **Detailed Error Reporting**: Clear error messages with file-specific details

## Installation

### Prerequisites

1. **Python 3.8 or newer** - [Download Python](https://www.python.org/downloads/)
2. **iTunes or Apple Mobile Device Support** - Required for iOS device connection
3. **iOS Device** with USB cable

### Installation Steps

1. Clone or download this repository
2. Open terminal/command prompt in the project folder
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. **Run the application**:
```bash
python main.py
```

2. **Connect iOS device**:
   - Connect iPhone/iPad to PC using USB cable
   - Unlock your iOS device
   - If prompted, select "Trust This Computer" on your iOS device

3. **Connect in the app**:
   - Click "Connect to iOS Device" button
   - Wait until status changes to "Connected"

4. **Load photos**:
   - Click "Load Photos from Device" button
   - Photos will appear in the list

5. **Select photos**:
   - Check photos you want to transfer (click checkbox in first column)
   - Use "Select All" or "Deselect All" for bulk selection
   - Shift+Click for range selection

6. **Configuration**:
   - Choose sorting mode: **Month_Year** or **Date_Month_Year**
   - Select "Output Base Path" - main folder where photos will be saved
   - Select "Unknown Folder Path" - folder for photos without dates
   - Choose duplicate handling: **overwrite**, **keep_both**, or **skip**

7. **Move photos**:
   - Click "Move Selected Photos" button
   - Confirm action
   - Process will run and progress will be displayed in the log

## Output Folder Structure

### Month_Year Mode:
```
Output Base Path/
├── 2024-01/
│   ├── IMG_001.jpg
│   └── IMG_002.jpg
├── 2024-02/
│   └── IMG_003.jpg
└── Unknown/
    └── IMG_004.jpg
```

### Date_Month_Year Mode:
```
Output Base Path/
├── 2024-01-15/
│   ├── IMG_001.jpg
│   └── IMG_002.jpg
├── 2024-01-20/
│   └── IMG_003.jpg
└── Unknown/
    └── IMG_004.jpg
```

## Configuration

The application saves configuration in `config.json`. You can:
- Change configuration through the UI
- Click "Save Configuration" to save settings
- Configuration will automatically load when the app starts

## Troubleshooting

### Device not detected
- Ensure USB cable is properly connected
- Ensure iOS device is unlocked
- Ensure you have selected "Trust This Computer" on your iOS device
- Ensure iTunes or Apple Mobile Device Support is installed
- Try unplugging and reconnecting the USB cable

### Photos not showing
- Ensure device is connected and trusted
- Try clicking "Load Photos from Device" again
- Check the log for detailed error messages

### Error while moving photos
- Ensure output path and unknown folder path are valid
- Ensure sufficient disk space is available
- Check the log for detailed error messages
- Review the ERROR DETAILS section at the end of the process

### Windows copy popup appears
- This is a Windows limitation when copying from MTP devices
- The popup cannot be completely suppressed
- The application will continue copying in the background

## Important Notes

- **Backup**: It's recommended to backup photos before transferring
- **Original Files**: This application **copies** photos from the device, not deletes them. Original photos remain on the iOS device
- **Duplicate Files**: Configurable behavior - overwrite, keep both, or skip
- **Metadata**: The application preserves original file creation and modification dates
- **Progress**: Real-time progress tracking with [X/Y] format and remaining count
- **Error Handling**: Detailed error reporting with file-specific information

## Technical Details

- **MTP Protocol**: Uses Windows Shell API to access iOS devices via MTP
- **Metadata Extraction**: Reads file properties from Windows Shell
- **Date Preservation**: Uses Win32 API to set file timestamps
- **Threading**: Background operations to prevent UI freezing
- **COM Initialization**: Proper COM handling for thread safety

## License

This application is created for personal use.

## Building Executable

To create a standalone `.exe` file for distribution:

### Quick Build (For Testing)

```bash
.\build_exe.bat
```

- Simple and fast
- Auto-detects dependencies
- Good for quick testing

### Advanced Build (For Distribution) ⭐ Recommended

```bash
.\build_advanced.bat
```

- Cleans previous builds
- Explicitly includes all dependencies
- Bundles README.md
- More reliable for distribution
- Recommended for sharing with users

### Manual Build

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "iOS-Photo-Mover" main.py
```

The executable will be created in `dist\iOS-Photo-Mover.exe` (~20 MB).

### Build Options

- `--onefile`: Bundle everything into a single .exe file
- `--windowed`: No console window (GUI only)
- `--name`: Name of the executable

### Distribution

After building:

1. **Test the executable**:
   - Run `dist\iOS-Photo-Mover.exe`
   - Test all features
   - Verify all dependencies work

2. **Distribute**:
   - Share the `iOS-Photo-Mover.exe` file
   - Users do NOT need Python installed
   - Users still need iTunes or Apple Mobile Device Support

### Build Troubleshooting

**Executable is too large**
- Normal size is ~20 MB due to Python runtime and dependencies
- This is expected for PyInstaller builds

**Missing modules error**
- Add the missing module with `--hidden-import module_name`

**Antivirus flags the .exe**
- Common with PyInstaller executables
- Sign the executable with a code signing certificate (optional)
- Users may need to add exception in their antivirus

**Application crashes on startup**
- Test on a clean Windows machine without Python
- Ensure iTunes/Apple Mobile Device Support is installed
- Use `--console` flag instead of `--windowed` for debugging

## Contributing

If you find bugs or want to add features, please create an issue or pull request.

## Requirements

### For Development:
- Python 3.8+
- pywin32
- hachoir (for metadata extraction)

See `requirements.txt` for complete list.

### For End Users (Executable):
- Windows 10 or later
- iTunes or Apple Mobile Device Support
- No Python installation required!
