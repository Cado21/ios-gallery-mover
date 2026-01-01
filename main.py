import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import shutil
from datetime import datetime
from pathlib import Path
import json
from typing import List, Dict, Optional, Tuple
import threading

import win32com.client
import win32file
import pywintypes
import pythoncom

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_AVAILABLE = True
except:
    HACHOIR_AVAILABLE = False

# Windows Portable Device support
WINDOWS_SUPPORT = True


class IOSPhotoMover:
    def __init__(self, root):
        self.root = root
        self.root.title("iOS Photo Mover")
        self.root.geometry("1000x900")
        
        self.selected_photos = []
        self.ios_device = None
        self.afc_service = None
        self.config = self.load_config()
        
        self.setup_ui()
        
    def load_config(self) -> Dict:
        """Load configuration from file"""
        config_file = Path("config.json")
        default_config = {
            "sort_mode": "Month_Year",
            "unknown_folder_path": str(Path.home() / "Pictures" / "iOS_Photos" / "Unknown"),
            "output_base_path": str(Path.home() / "Pictures" / "iOS_Photos"),
            "duplicate_mode": "overwrite"  # "overwrite", "keep_both", or "skip"
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        config_file = Path("config.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Make scrollable frame fill canvas width
        def _configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _configure_canvas)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Main container inside scrollable frame
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollable_frame.columnconfigure(0, weight=1)
        scrollable_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # iOS Connection Section
        conn_frame = ttk.LabelFrame(main_frame, text="iOS Device Connection", padding="10")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.connection_status = ttk.Label(conn_frame, text="Status: Not Connected", foreground="red")
        self.connection_status.grid(row=0, column=0, sticky=tk.W, padx=5)
        
        ttk.Button(conn_frame, text="Connect to iOS Device", command=self.connect_device).grid(row=0, column=1, padx=5)
        ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_device).grid(row=0, column=2, padx=5)
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        config_frame.columnconfigure(1, weight=1)
        
        # Sort Mode
        ttk.Label(config_frame, text="Sort By:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.sort_mode = tk.StringVar(value=self.config.get("sort_mode", "Month_Year"))
        sort_combo = ttk.Combobox(config_frame, textvariable=self.sort_mode, 
                                  values=["Month_Year", "Date_Month_Year"], state="readonly", width=20)
        sort_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.update_config())
        
        # Output Base Path
        ttk.Label(config_frame, text="Output Base Path:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_path_var = tk.StringVar(value=self.config.get("output_base_path", ""))
        ttk.Entry(config_frame, textvariable=self.output_path_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(config_frame, text="Browse", command=self.browse_output_path).grid(row=1, column=2, padx=5)
        
        # Unknown Folder Path
        ttk.Label(config_frame, text="Unknown Folder Path:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.unknown_path_var = tk.StringVar(value=self.config.get("unknown_folder_path", ""))
        ttk.Entry(config_frame, textvariable=self.unknown_path_var, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(config_frame, text="Browse", command=self.browse_unknown_path).grid(row=2, column=2, padx=5)
        
        # Duplicate File Handling
        ttk.Label(config_frame, text="If File Exists:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.duplicate_mode = tk.StringVar(value=self.config.get("duplicate_mode", "overwrite"))
        duplicate_combo = ttk.Combobox(config_frame, textvariable=self.duplicate_mode, 
                                      values=["overwrite", "keep_both", "skip"], state="readonly", width=20)
        duplicate_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        duplicate_combo.bind("<<ComboboxSelected>>", lambda e: self.update_config())
        
        # Add tooltip/explanation
        ttk.Label(config_frame, text="(overwrite = replace, keep_both = rename to file_1.mov, skip = don't copy)", 
                 font=("Arial", 8), foreground="gray").grid(row=4, column=1, sticky=tk.W, padx=5)
        
        # Photo Selection Section
        photo_frame = ttk.LabelFrame(main_frame, text="Photo Selection", padding="10")
        photo_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        photo_frame.columnconfigure(0, weight=1)
        photo_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Buttons for photo selection
        btn_frame = ttk.Frame(photo_frame)
        btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(btn_frame, text="Load Photos from Device", command=self.load_photos).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Select All", command=self.select_all_photos).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Deselect All", command=self.deselect_all_photos).grid(row=0, column=2, padx=5)
        ttk.Label(btn_frame, text="Selected:").grid(row=0, column=3, padx=(10, 0))
        self.selected_count_label = ttk.Label(btn_frame, text="0")
        self.selected_count_label.grid(row=0, column=4, padx=(0, 5))
        
        # Photo list with checkboxes
        list_frame = ttk.Frame(photo_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview for photo list
        columns = ("Photo", "Type", "Date", "Size")
        self.photo_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=15)
        self.photo_tree.heading("#0", text="Select")
        self.photo_tree.heading("Photo", text="Photo Name")
        self.photo_tree.heading("Type", text="Type")
        self.photo_tree.heading("Date", text="Month (YYYY-MM)")
        self.photo_tree.heading("Size", text="Size")
        
        self.photo_tree.column("#0", width=60, anchor="center")
        self.photo_tree.column("Photo", width=250)
        self.photo_tree.column("Type", width=80)
        self.photo_tree.column("Date", width=120)
        self.photo_tree.column("Size", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.photo_tree.yview)
        self.photo_tree.configure(yscrollcommand=scrollbar.set)
        
        self.photo_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind events
        self.photo_tree.bind("<Button-1>", self.on_tree_click)
        self.photo_tree.bind("<Shift-Button-1>", self.on_shift_click)
        self.last_selected_item = None  # Track last selected for shift-click
        
        # Action Section
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(action_frame, text="Move Selected Photos", command=self.move_photos, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Save Configuration", command=self.save_config).pack(side=tk.LEFT, padx=5)
        
        # Progress/Log Section (much bigger now)
        log_frame = ttk.LabelFrame(main_frame, text="Progress Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.photo_data = {}  # Store photo metadata
    
    def log(self, message: str):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def connect_device(self):
        """Connect to iOS device via Windows Explorer"""
        try:
            self.log("Searching for iOS devices...")
            
            # Find iOS device in Windows Portable Devices
            shell = win32com.client.Dispatch("Shell.Application")
            
            # Look for iPhone in "This PC"
            this_pc = shell.NameSpace(17)  # 17 = ssfDRIVES (This PC)
            
            ios_device_path = None
            device_name = None
            
            # Search for iPhone/iPad
            for item in this_pc.Items():
                item_name = item.Name.lower()
                if 'iphone' in item_name or 'ipad' in item_name or 'apple' in item_name:
                    ios_device_path = item.Path
                    device_name = item.Name
                    break
            
            if not ios_device_path:
                messagebox.showwarning("No Device", "No iOS device found. Please:\n"
                                  "1. Connect your iOS device via USB\n"
                                  "2. Unlock your device\n"
                                  "3. Trust this computer if prompted\n"
                                  "4. Make sure the device appears in Windows Explorer")
                self.connection_status.config(text="Status: Not Connected", foreground="red")
                return
            
            self.log(f"Found device: {device_name}")
            self.ios_device = ios_device_path
            self.device_name = device_name
            
            self.connection_status.config(text=f"Status: Connected ({device_name})", foreground="green")
            self.log("Device connected successfully!")
            
        except Exception as e:
            error_msg = f"Failed to connect: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Connection Error", error_msg)
            self.connection_status.config(text="Status: Connection Failed", foreground="red")
    
    def disconnect_device(self):
        """Disconnect from iOS device"""
        self.ios_device = None
        self.device_name = None
        self.connection_status.config(text="Status: Not Connected", foreground="red")
        self.log("Device disconnected")
    
    def scan_folder_recursive(self, shell, folder_item, all_photos, depth=0):
        """Recursively scan folder for photos using GetFolder method"""
        if depth > 5:  # Prevent infinite recursion
            self.log(f"{'  ' * depth}Max depth reached at: {folder_item.Name}")
            return
        
        try:
            self.log(f"{'  ' * depth}Accessing: {folder_item.Name}")
            
            # Try GetFolder method (works for MTP devices)
            try:
                folder = folder_item.GetFolder
                if folder:
                    items_list = list(folder.Items())
                    self.log(f"{'  ' * depth}Found {len(items_list)} items in {folder_item.Name}")
                    
                    for item in items_list:
                        try:
                            if item.IsFolder:
                                self.log(f"{'  ' * depth}  Subfolder: {item.Name}")
                                # Recursively scan subfolder
                                if depth < 3:
                                    self.scan_folder_recursive(shell, item, all_photos, depth + 1)
                            else:
                                filename = item.Name
                                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.mov', '.mp4')):
                                    self.log(f"{'  ' * depth}  ✓ Photo: {filename}")
                                    # Store folder reference and folder name for getting details later
                                    all_photos.append((item.Path, item, folder, folder_item.Name))
                        except Exception as e:
                            self.log(f"{'  ' * depth}  Error with {item.Name}: {e}")
                            continue
                else:
                    self.log(f"{'  ' * depth}GetFolder returned None")
            except Exception as e:
                self.log(f"{'  ' * depth}GetFolder failed: {e}")
                
        except Exception as e:
            self.log(f"{'  ' * depth}Error scanning folder: {e}")
    
    def load_photos(self):
        """Load photos from iOS device"""
        if not self.ios_device:
            messagebox.showwarning("Not Connected", "Please connect to an iOS device first.")
            return
        
        try:
            self.log("Loading photos from device...")
            self.photo_tree.delete(*self.photo_tree.get_children())
            self.photo_data = {}
            
            # Access device using Windows Shell
            shell = win32com.client.Dispatch("Shell.Application")
            device_folder = shell.NameSpace(self.ios_device)
            
            if not device_folder:
                messagebox.showerror("Error", "Cannot access device. Please reconnect.")
                return
            
            # Find Internal Storage
            internal_storage = None
            self.log("Searching for Internal Storage...")
            
            for item in device_folder.Items():
                item_name = item.Name.lower()
                self.log(f"Found: {item.Name}")
                if 'internal' in item_name or 'storage' in item_name:
                    internal_storage = item
                    break
            
            if not internal_storage:
                # Try first item (usually Internal Storage)
                items = list(device_folder.Items())
                if items:
                    internal_storage = items[0]
                    self.log(f"Using first item: {internal_storage.Name}")
            
            if not internal_storage:
                messagebox.showerror("Error", "Cannot find Internal Storage on device.\n\n"
                                   "Please:\n"
                                   "1. Unlock your iPhone\n"
                                   "2. Trust this computer (check iPhone screen)\n"
                                   "3. Wait a moment and try again")
                return
            
            self.log(f"Accessing: {internal_storage.Name}")
            
            # Try to get FolderItem interface
            all_photos = []
            self.log("Scanning for photos...")
            
            # Method 1: Try GetFolder property
            try:
                self.log("Method 1: Trying GetFolder...")
                folder = internal_storage.GetFolder
                if folder:
                    self.log(f"GetFolder successful: {folder}")
                    items = list(folder.Items())
                    self.log(f"Found {len(items)} folders/files")
                    
                    for item in items:
                        self.log(f"Scanning: {item.Name}")
                        if item.IsFolder:
                            # Scan this folder for photos
                            self.scan_folder_recursive(shell, item, all_photos, 0)
                        else:
                            # Check if it's a photo file
                            filename = item.Name
                            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.mov', '.mp4')):
                                self.log(f"✓ Photo found: {filename}")
                                all_photos.append((item.Path, item))
            except Exception as e:
                self.log(f"GetFolder failed: {e}")
            
            # Method 2: Try direct Items() access
            try:
                self.log("Method 2: Trying direct Items()...")
                items = internal_storage.Items()
                if items:
                    self.log(f"Items() successful, count: {items.Count}")
                    for i in range(items.Count):
                        item = items.Item(i)
                        self.log(f"Item {i}: {item.Name} (IsFolder: {item.IsFolder})")
                        
                        if item.IsFolder:
                            # Try to access this folder
                            self.scan_folder_recursive(shell, item, all_photos, 0)
            except Exception as e:
                self.log(f"Items() failed: {e}")
            
            # Method 3: Try using the path directly
            try:
                self.log("Method 3: Trying path-based access...")
                storage_path = internal_storage.Path
                self.log(f"Storage path: {storage_path}")
                
                storage_namespace = shell.NameSpace(storage_path)
                if storage_namespace:
                    self.log("Path-based namespace successful!")
                    items = list(storage_namespace.Items())
                    self.log(f"Found {len(items)} items via path")
                    
                    for item in items:
                        self.log(f"Path item: {item.Name}")
                        if item.IsFolder:
                            self.scan_folder_recursive(shell, item, all_photos, 0)
                else:
                    self.log("Path-based namespace returned None")
            except Exception as e:
                self.log(f"Path-based access failed: {e}")
            
            if not all_photos:
                messagebox.showinfo("No Photos", 
                                  "No photos found on the device.\n\n"
                                  "This could mean:\n"
                                  "1. No photos in Camera Roll\n"
                                  "2. iPhone needs to be unlocked\n"
                                  "3. Computer not trusted on iPhone\n"
                                  "4. Windows MTP driver issue")
                return
            
            self.log(f"Found {len(all_photos)} photos, loading metadata...")
            
            # Load photo metadata
            total_photos = len(all_photos)
            
            # Debug: Check first file for available columns and folder info
            if all_photos:
                self.log("Checking available metadata columns...")
                try:
                    _, first_file, first_folder = all_photos[0]
                    
                    # Check folder name
                    try:
                        if hasattr(first_file, 'Parent'):
                            parent_path = first_file.Parent.Path
                            self.log(f"  Parent folder path: {parent_path}")
                            folder_name = Path(parent_path).name
                            self.log(f"  Parent folder name: {folder_name}")
                    except Exception as e:
                        self.log(f"  Cannot get parent folder: {e}")
                    
                    # Check columns
                    for col in range(31):
                        try:
                            detail = first_folder.GetDetailsOf(first_file, col)
                            if detail and detail.strip():
                                self.log(f"  Column {col}: {detail[:50]}")  # Show first 50 chars
                        except:
                            pass
                except:
                    pass
            
            for idx, item_data in enumerate(all_photos):
                try:
                    file_path, file_obj, parent_folder, folder_name = item_data
                    filename = file_obj.Name
                    
                    # Get file type
                    file_ext = filename.split('.')[-1].upper() if '.' in filename else 'Unknown'
                    
                    # Get file size using GetDetailsOf - try multiple columns
                    file_size = 0
                    size_str = "Unknown"
                    
                    # Try to get actual size in bytes from different columns
                    for col in [1, 2]:  # Column 1 or 2 might have size
                        try:
                            size_detail = parent_folder.GetDetailsOf(file_obj, col)
                            if size_detail and size_detail.strip():
                                size_detail = size_detail.strip()
                                
                                # Check if it's actually a size (contains KB, MB, GB, or bytes)
                                if any(unit in size_detail for unit in ['KB', 'MB', 'GB', 'byte']):
                                    # Parse size string
                                    if 'KB' in size_detail:
                                        file_size = int(float(size_detail.replace('KB', '').replace(',', '').strip()) * 1024)
                                    elif 'MB' in size_detail:
                                        file_size = int(float(size_detail.replace('MB', '').replace(',', '').strip()) * 1024 * 1024)
                                    elif 'GB' in size_detail:
                                        file_size = int(float(size_detail.replace('GB', '').replace(',', '').strip()) * 1024 * 1024 * 1024)
                                    elif 'byte' in size_detail.lower():
                                        file_size = int(size_detail.split()[0].replace(',', ''))
                                    
                                    if file_size > 0:
                                        size_str = self.format_size(file_size)
                                        break
                        except:
                            continue
                    
                    # Get date - try all columns from 0 to 30
                    date_str = "Unknown"
                    for col in range(31):
                        try:
                            date_detail = parent_folder.GetDetailsOf(file_obj, col)
                            if date_detail and date_detail.strip():
                                date_detail = date_detail.strip()
                                
                                # Check if it looks like a date (contains / or - and has digits)
                                if ('/' in date_detail or '-' in date_detail or ':' in date_detail) and any(c.isdigit() for c in date_detail):
                                    # Try to parse various date formats
                                    date_formats = [
                                        "%m/%d/%Y %I:%M %p", "%m/%d/%Y %I:%M:%S %p",
                                        "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S",
                                        "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
                                        "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d",
                                        "%d-%m-%Y", "%m-%d-%Y", "%Y%m%d",
                                        "%-m/%-d/%Y %-I:%M %p", "%-m/%-d/%Y",  # Without leading zeros
                                    ]
                                    
                                    for fmt in date_formats:
                                        try:
                                            # Extract just the date part if there's time
                                            date_part = date_detail
                                            if ' ' in date_detail and ':' in date_detail:
                                                # Has time, extract date part
                                                parts = date_detail.split()
                                                if len(parts) >= 1:
                                                    date_part = parts[0]
                                            
                                            dt = datetime.strptime(date_part, fmt.split()[0] if ' ' in fmt else fmt)
                                            date_str = dt.strftime("%Y-%m-%d")
                                            break
                                        except:
                                            continue
                                    
                                    if date_str != "Unknown":
                                        break
                        except:
                            continue
                    
                    # Fallback 1: Extract date from filename
                    if date_str == "Unknown":
                        try:
                            if filename.startswith("IMG_") or filename.startswith("VID_"):
                                parts = filename.split("_")
                                if len(parts) >= 2:
                                    date_part = parts[1].replace("E", "")  # Remove E from IMG_E prefix
                                    if len(date_part) >= 8 and date_part[:8].isdigit():
                                        year = date_part[:4]
                                        month = date_part[4:6]
                                        day = date_part[6:8]
                                        date_str = f"{year}-{month}-{day}"
                        except:
                            pass
                    
                    # Fallback 2: Extract date from parent folder name (e.g., 202512__, 202410__)
                    if date_str == "Unknown" and folder_name:
                        try:
                            # Check if folder name starts with YYYYMM format
                            if len(folder_name) >= 6 and folder_name[:6].isdigit():
                                year = folder_name[:4]
                                month = folder_name[4:6]
                                # Use first day of month as default
                                date_str = f"{year}-{month}-01"
                        except:
                            pass
                    
                    # Use larger checkbox symbols
                    photo_id = self.photo_tree.insert("", tk.END, text="□", 
                                                      values=(filename, file_ext, date_str, size_str))
                    self.photo_data[photo_id] = {
                        'path': file_path,
                        'file_obj': file_obj,
                        'parent_folder': parent_folder,
                        'filename': filename,
                        'date': date_str,
                        'size': file_size,
                        'type': file_ext
                    }
                    
                    # Update UI every 50 photos to keep responsive
                    if idx % 50 == 0:
                        self.root.update_idletasks()
                        
                except Exception as e:
                    self.log(f"Error loading metadata: {e}")
                    continue
            
            self.log(f"✓ Loaded {len(self.photo_data)} photos successfully!")
            
        except Exception as e:
            error_msg = f"Failed to load photos: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def extract_date_from_file(self, file_obj) -> str:
        """Extract date from file object"""
        filename = file_obj.Name
        
        # Method 1: Try to get date from file properties
        try:
            # Try ModifyDate property
            date_modified = file_obj.ModifyDate
            if date_modified and str(date_modified) != "":
                # Try different date formats
                for fmt in ["%m/%d/%Y %I:%M:%S %p", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"]:
                    try:
                        dt = datetime.strptime(str(date_modified), fmt)
                        return dt.strftime("%Y-%m-%d")
                    except:
                        continue
        except:
            pass
        
        # Method 2: Try GetDetailsOf for DateTaken or DateModified
        try:
            # This might work for some files
            parent_folder = file_obj.Parent
            if parent_folder:
                shell = win32com.client.Dispatch("Shell.Application")
                folder = shell.NameSpace(parent_folder.Path)
                if folder:
                    # Column 12 is usually DateTaken, 3 is DateModified
                    for col in [12, 3]:
                        try:
                            date_str = folder.GetDetailsOf(file_obj, col)
                            if date_str and date_str.strip():
                                # Try to parse it
                                for fmt in ["%m/%d/%Y %I:%M:%S %p", "%Y-%m-%d", "%d/%m/%Y"]:
                                    try:
                                        dt = datetime.strptime(date_str.strip(), fmt)
                                        return dt.strftime("%Y-%m-%d")
                                    except:
                                        continue
                        except:
                            continue
        except:
            pass
        
        # Method 3: Extract from filename (IMG_YYYYMMDD format)
        try:
            if filename.startswith("IMG_") or filename.startswith("VID_"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    date_part = parts[1].replace("E", "")  # Remove E from IMG_E prefix
                    if len(date_part) >= 8 and date_part[:8].isdigit():
                        year = date_part[:4]
                        month = date_part[4:6]
                        day = date_part[6:8]
                        return f"{year}-{month}-{day}"
        except:
            pass
        
        return "Unknown"
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def on_tree_click(self, event):
        """Handle click on treeview - toggle selection"""
        # identify_row takes only y coordinate
        item = self.photo_tree.identify_row(event.y)
        column = self.photo_tree.identify_column(event.x)
        
        if item:
            # Only toggle if clicking on checkbox column
            if column == "#0":
                # Toggle checkbox
                current = self.photo_tree.item(item, "text")
                new_text = "☑" if current == "□" else "□"
                self.photo_tree.item(item, text=new_text)
                self.update_selected_count()
                self.last_selected_item = item
            # Allow default selection behavior for other columns
    
    def on_shift_click(self, event):
        """Handle shift+click for range selection"""
        # identify_row takes only y coordinate
        item = self.photo_tree.identify_row(event.y)
        column = self.photo_tree.identify_column(event.x)
        
        # Only work on checkbox column
        if item and column == "#0" and self.last_selected_item:
            # Get all items
            all_items = self.photo_tree.get_children()
            
            try:
                # Find indices
                start_idx = all_items.index(self.last_selected_item)
                end_idx = all_items.index(item)
                
                # Ensure start is before end
                if start_idx > end_idx:
                    start_idx, end_idx = end_idx, start_idx
                
                # Select all items in range
                for i in range(start_idx, end_idx + 1):
                    self.photo_tree.item(all_items[i], text="☑")
                
                self.update_selected_count()
                self.last_selected_item = item
            except ValueError:
                pass
    
    def select_all_photos(self):
        """Select all photos"""
        for item in self.photo_tree.get_children():
            self.photo_tree.item(item, text="☑")
        self.update_selected_count()
    
    def deselect_all_photos(self):
        """Deselect all photos"""
        for item in self.photo_tree.get_children():
            self.photo_tree.item(item, text="□")
        self.update_selected_count()
    
    def update_selected_count(self):
        """Update selected photo count"""
        count = sum(1 for item in self.photo_tree.get_children() 
                   if self.photo_tree.item(item, "text") == "☑")
        self.selected_count_label.config(text=str(count))
    
    def browse_output_path(self):
        """Browse for output base path"""
        path = filedialog.askdirectory(title="Select Output Base Path")
        if path:
            self.output_path_var.set(path)
            self.update_config()
    
    def browse_unknown_path(self):
        """Browse for unknown folder path"""
        path = filedialog.askdirectory(title="Select Unknown Folder Path")
        if path:
            self.unknown_path_var.set(path)
            self.update_config()
    
    def update_config(self):
        """Update configuration from UI"""
        self.config["sort_mode"] = self.sort_mode.get()
        self.config["output_base_path"] = self.output_path_var.get()
        self.config["unknown_folder_path"] = self.unknown_path_var.get()
        self.config["duplicate_mode"] = self.duplicate_mode.get()
    
    def get_photo_date(self, photo_info: Dict) -> Optional[datetime]:
        """Get date from photo metadata"""
        date_str = photo_info.get('date', '')
        
        if date_str == "Unknown":
            return None
        
        # Try to parse date string
        try:
            # Format: YYYY-MM-DD
            if len(date_str) == 10 and date_str.count('-') == 2:
                return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            pass
        
        return None
    
    def get_destination_folder(self, photo_info: Dict, base_path: str) -> Path:
        """Get destination folder based on sort mode"""
        photo_date = self.get_photo_date(photo_info)
        
        if photo_date is None:
            # Unknown date - use unknown folder
            unknown_path = Path(self.unknown_path_var.get())
            unknown_path.mkdir(parents=True, exist_ok=True)
            return unknown_path
        
        base = Path(base_path)
        sort_mode = self.sort_mode.get()
        
        if sort_mode == "Month_Year":
            # Format: YYYY-MM (e.g., 2024-01)
            folder_name = photo_date.strftime("%Y-%m")
        elif sort_mode == "Date_Month_Year":
            # Format: YYYY-MM-DD (e.g., 2024-01-15)
            folder_name = photo_date.strftime("%Y-%m-%d")
        else:
            folder_name = "Unknown"
        
        destination = base / folder_name
        destination.mkdir(parents=True, exist_ok=True)
        return destination
    
    def get_media_creation_date_from_file(self, file_path: Path):
        """Get media creation date from copied file using Shell"""
        try:
            shell = win32com.client.Dispatch("Shell.Application")
            folder = shell.NameSpace(str(file_path.parent))
            file_item = folder.ParseName(file_path.name)
            
            if file_item:
                # Try different columns that might contain media creation date
                # Column 208 = Media created
                for col in [208, 12, 4, 3]:
                    try:
                        detail = folder.GetDetailsOf(file_item, col)
                        if detail and detail.strip():
                            detail = detail.strip()
                            
                            # Try to parse date
                            date_formats = [
                                "%m/%d/%Y %I:%M %p",
                                "%m/%d/%Y %I:%M:%S %p",
                                "%d/%m/%Y %H:%M",
                                "%d/%m/%Y %H:%M:%S",
                                "%Y-%m-%d %H:%M:%S",
                                "%m/%d/%Y",
                                "%d/%m/%Y",
                                "%Y-%m-%d",
                                "%d-%b-%y %I:%M %p",
                                "%d-%b-%Y %I:%M %p",
                            ]
                            
                            for fmt in date_formats:
                                try:
                                    dt = datetime.strptime(detail, fmt)
                                    if dt.year < 100:
                                        dt = dt.replace(year=dt.year + 2000)
                                    self.log(f"  Found media date (col {col}): {detail}")
                                    return dt
                                except:
                                    continue
                    except:
                        continue
        except Exception as e:
            pass
        
        return None
    
    def get_media_creation_date(self, file_path: Path):
        """Extract media creation date from video/photo file"""
        try:
            if not HACHOIR_AVAILABLE:
                return None
            
            # Parse file
            parser = createParser(str(file_path))
            if not parser:
                return None
            
            # Extract metadata
            metadata = extractMetadata(parser)
            if not metadata:
                return None
            
            # Try to get creation date
            if hasattr(metadata, 'creation_date') and metadata.creation_date:
                return metadata.creation_date
            
            # Try to get datetime
            if hasattr(metadata, 'datetime') and metadata.datetime:
                return metadata.datetime
            
            # Try to get last_modification
            if hasattr(metadata, 'last_modification') and metadata.last_modification:
                return metadata.last_modification
            
            parser.stream._input.close()
            
        except Exception as e:
            pass
        
        return None
    
    def preserve_file_metadata(self, file_obj, dest_file: Path, parent_folder):
        """Preserve file creation and modification dates from source"""
        try:
            # Method 1: Try to read metadata from the copied file using Shell
            self.log(f"  Reading file metadata...")
            
            # First try: Windows Shell GetDetailsOf on copied file
            media_date = self.get_media_creation_date_from_file(dest_file)
            
            # Second try: Hachoir parser
            if not media_date:
                media_date = self.get_media_creation_date(dest_file)
            
            if media_date:
                # Use media creation date
                file_time = pywintypes.Time(media_date)
                
                handle = win32file.CreateFile(
                    str(dest_file),
                    win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None
                )
                
                win32file.SetFileTime(handle, file_time, None, file_time)
                win32file.CloseHandle(handle)
                
                self.log(f"  ✓ Set date from media metadata: {media_date.strftime('%Y-%m-%d %H:%M:%S')}")
                return True
            
            # Method 2: Try to get date from MTP metadata columns
            date_modified = None
            
            # Method 2: Try to get date from MTP metadata columns
            date_modified = None
            
            # Debug: Log all columns for first file (commented out to reduce spam)
            # self.log(f"  Scanning metadata columns for {file_obj.Name}...")
            
            # Scan all columns to find date information
            for col in range(50):  # Try more columns
                try:
                    detail = parent_folder.GetDetailsOf(file_obj, col)
                    if detail and detail.strip():
                        detail = detail.strip()
                        
                        # Log all non-empty columns for debugging (commented out)
                        # if col < 20:  # Only log first 20 to avoid spam
                        #     self.log(f"    Col {col}: {detail[:60]}")
                        
                        # Check if it looks like a date
                        if ('/' in detail or '-' in detail) and any(c.isdigit() for c in detail):
                            # Try to parse various date formats
                            date_formats = [
                                "%m/%d/%Y %I:%M %p",
                                "%m/%d/%Y %I:%M:%S %p", 
                                "%d/%m/%Y %H:%M",
                                "%d/%m/%Y %H:%M:%S",
                                "%Y-%m-%d %H:%M:%S",
                                "%m/%d/%Y",
                                "%d/%m/%Y",
                                "%Y-%m-%d",
                                "%d-%b-%y %I:%M %p",  # 30-Dec-25 7:27 PM
                                "%d-%b-%Y %I:%M %p",
                            ]
                            
                            for fmt in date_formats:
                                try:
                                    dt = datetime.strptime(detail, fmt)
                                    # If year is in 2-digit format, adjust
                                    if dt.year < 100:
                                        dt = dt.replace(year=dt.year + 2000)
                                    date_modified = dt
                                    self.log(f"  ✓ Found date in column {col}: {detail}")
                                    break
                                except:
                                    continue
                            
                            if date_modified:
                                break
                except:
                    continue
            
            # If we found a date, apply it
            if date_modified:
                # Use same date for both created and modified
                created_time = pywintypes.Time(date_modified)
                modified_time = pywintypes.Time(date_modified)
                
                handle = win32file.CreateFile(
                    str(dest_file),
                    win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None
                )
                
                win32file.SetFileTime(handle, created_time, None, modified_time)
                win32file.CloseHandle(handle)
                
                self.log(f"  ✓ Set date: {date_modified.strftime('%Y-%m-%d %H:%M:%S')}")
                return True
            
            # Fallback: Use folder name date
            photo_info = None
            for item_id, data in self.photo_data.items():
                if data.get('filename') == file_obj.Name:
                    photo_info = data
                    break
            
            if photo_info and photo_info.get('date') != "Unknown":
                date_str = photo_info['date']
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    dt = dt.replace(hour=12, minute=0, second=0)
                    
                    file_time = pywintypes.Time(dt)
                    
                    handle = win32file.CreateFile(
                        str(dest_file),
                        win32file.GENERIC_WRITE,
                        0,
                        None,
                        win32file.OPEN_EXISTING,
                        0,
                        None
                    )
                    
                    win32file.SetFileTime(handle, file_time, None, file_time)
                    win32file.CloseHandle(handle)
                    
                    self.log(f"  Set date from folder: {date_str}")
                    return True
                except Exception as e:
                    self.log(f"  Could not set date: {e}")
            
            self.log(f"  Warning: No date found, file will have current date")
            return False
                
        except Exception as e:
            self.log(f"  Error preserving metadata: {e}")
            return False
    
    def move_photos(self):
        """Move selected photos to organized folders"""
        selected_items = [item for item in self.photo_tree.get_children() 
                         if self.photo_tree.item(item, "text") == "☑"]
        
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select at least one photo to move.")
            return
        
        # Update config
        self.update_config()
        
        # Validate paths
        output_path = self.output_path_var.get()
        if not output_path:
            messagebox.showerror("Error", "Please set Output Base Path.")
            return
        
        unknown_path = self.unknown_path_var.get()
        if not unknown_path:
            messagebox.showerror("Error", "Please set Unknown Folder Path.")
            return
        
        # Confirm action
        if not messagebox.askyesno("Confirm", f"Move {len(selected_items)} photo(s) to organized folders?"):
            return
        
        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=self._move_photos_thread, args=(selected_items,))
        thread.daemon = True
        thread.start()
    
    def _move_photos_thread(self, selected_items: List[str]):
        """Move photos in background thread"""
        # Initialize COM for this thread
        pythoncom.CoInitialize()
        
        try:
            moved_count = 0
            error_count = 0
            skipped_count = 0
            total_files = len(selected_items)
            error_details = []  # Store error details for summary
            
            for idx, item in enumerate(selected_items, 1):
                try:
                    photo_info = self.photo_data[item]
                    filename = photo_info['filename']
                    source_path = photo_info['path']
                    parent_folder = photo_info.get('parent_folder')  # Get parent folder for metadata
                    
                    # Get destination folder
                    dest_folder = self.get_destination_folder(photo_info, self.output_path_var.get())
                    dest_path = dest_folder / filename
                    
                    remaining = total_files - idx + 1
                    self.log(f"[{idx}/{total_files}] Moving {filename} to {dest_folder}... ({remaining} remaining)")
                    
                    # Copy file from iOS device
                    try:
                        import time
                        file_obj = photo_info['file_obj']
                        shell = win32com.client.Dispatch("Shell.Application")
                        
                        # Handle duplicate files based on config
                        expected_file = dest_folder / filename
                        duplicate_mode = self.config.get("duplicate_mode", "overwrite")
                        
                        if expected_file.exists():
                            if duplicate_mode == "skip":
                                self.log(f"  ⊘ Skipped: {filename} (already exists)")
                                skipped_count += 1
                                continue
                            elif duplicate_mode == "overwrite":
                                self.log(f"  File exists, overwriting...")
                                expected_file.unlink()
                            elif duplicate_mode == "keep_both":
                                # Find available filename
                                counter = 1
                                stem = expected_file.stem
                                suffix = expected_file.suffix
                                while expected_file.exists():
                                    expected_file = dest_folder / f"{stem}_{counter}{suffix}"
                                    counter += 1
                                self.log(f"  File exists, renaming to {expected_file.name}...")
                                # We'll need to rename after copy
                        
                        self.log(f"  Copying {filename}...")
                        
                        # Get destination folder namespace
                        dest_folder_obj = shell.NameSpace(str(dest_folder))
                        if not dest_folder_obj:
                            error_msg = f"Cannot access destination: {dest_folder}"
                            self.log(f"✗ {error_msg}")
                            error_details.append(f"{filename}: {error_msg}")
                            error_count += 1
                            continue
                        
                        # Direct copy with flags (popup will appear, but that's unavoidable with MTP)
                        # FOF_NOCONFIRMATION (0x0010) = Yes to all
                        dest_folder_obj.CopyHere(file_obj, 16)
                        
                        # Wait for file
                        max_wait = 120
                        wait_time = 0
                        check_interval = 1
                        last_log_time = 0
                        
                        copied_file = dest_folder / filename
                        
                        while wait_time < max_wait:
                            if copied_file.exists():
                                time.sleep(2)
                                size1 = copied_file.stat().st_size
                                time.sleep(1)
                                size2 = copied_file.stat().st_size
                                
                                if size1 == size2 and size1 > 0:
                                    final_file = copied_file
                                    
                                    # Rename if needed for keep_both mode
                                    if duplicate_mode == "keep_both" and expected_file != copied_file:
                                        if expected_file.exists():
                                            expected_file.unlink()
                                        shutil.move(str(copied_file), str(expected_file))
                                        final_file = expected_file
                                    
                                    # Preserve metadata
                                    try:
                                        if parent_folder:
                                            self.preserve_file_metadata(file_obj, final_file, parent_folder)
                                    except Exception as e:
                                        self.log(f"  Warning: Could not preserve metadata: {e}")
                                    
                                    display_name = final_file.name if final_file != copied_file else filename
                                    self.log(f"✓ Moved: {display_name} ({self.format_size(size2)})")
                                    moved_count += 1
                                    break
                            
                            time.sleep(check_interval)
                            wait_time += check_interval
                            
                            if wait_time - last_log_time >= 10:
                                self.log(f"  Still copying... ({wait_time}s)")
                                last_log_time = wait_time
                        else:
                            error_msg = f"Timeout after {max_wait}s - file may still be copying"
                            self.log(f"✗ {error_msg}")
                            error_details.append(f"{filename}: {error_msg}")
                            error_count += 1
                                
                    except Exception as copy_error:
                        error_msg = str(copy_error)
                        self.log(f"✗ Copy error: {error_msg}")
                        error_details.append(f"{filename}: {error_msg}")
                        error_count += 1
                        
                except Exception as e:
                    error_msg = str(e)
                    self.log(f"✗ Error moving {photo_info.get('filename', 'unknown')}: {error_msg}")
                    error_details.append(f"{photo_info.get('filename', 'unknown')}: {error_msg}")
                    error_count += 1
            
            # Summary
            self.log(f"\n{'='*60}")
            self.log(f"SUMMARY:")
            self.log(f"  ✓ Moved: {moved_count}")
            self.log(f"  ⊘ Skipped: {skipped_count}")
            self.log(f"  ✗ Errors: {error_count}")
            
            # Show error details if any
            if error_details:
                self.log(f"\nERROR DETAILS:")
                for error in error_details:
                    self.log(f"  • {error}")
            
            self.log(f"{'='*60}\n")
            
            # Show messagebox
            msg = f"Photo moving completed!\n\nMoved: {moved_count}\nSkipped: {skipped_count}\nErrors: {error_count}"
            if error_details:
                msg += f"\n\nError details are shown in the log above."
            messagebox.showinfo("Complete", msg)
            
        except Exception as e:
            self.log(f"Fatal error: {e}")
            messagebox.showerror("Error", f"Failed to move photos: {e}")
        finally:
            # Uninitialize COM
            pythoncom.CoUninitialize()


def main():
    root = tk.Tk()
    app = IOSPhotoMover(root)
    root.mainloop()


if __name__ == "__main__":
    main()

