import random
import shutil
import re
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, font
from concurrent.futures import ThreadPoolExecutor
import asyncio
import time
from datetime import datetime
from tkinter import PhotoImage
import os

class ModernTheme:
    # Color scheme
    PRIMARY = "#2C3E50"  # Dark blue-gray
    SECONDARY = "#3498DB"  # Bright blue
    ACCENT = "#E74C3C"  # Red
    BACKGROUND = "#ECF0F1"  # Light gray
    TEXT_PRIMARY = "#2C3E50"  # Dark blue-gray
    TEXT_SECONDARY = "#7F8C8D"  # Gray
    SUCCESS = "#27AE60"  # Green
    WARNING = "#F39C12"  # Orange
    
    # Table specific colors
    TABLE_HEADER_BG = "#34495e"  # Darker blue-gray for header
    TABLE_HEADER_FG = "#ffffff"  # White text for header
    TABLE_ROW_SELECTED = "#3498db"  # Blue for selected row
    TABLE_ROW_HOVER = "#d5dbdb"    # Light gray for hover
    
    # Font configurations
    FONT_FAMILY = "Helvetica"
    FONT_SIZE_LARGE = 14
    FONT_SIZE_MEDIUM = 12
    FONT_SIZE_SMALL = 10

    @classmethod
    def configure_styles(cls):
        style = ttk.Style()
        
        # Configure the main Treeview style
        style.configure(
            "Custom.Treeview",
            background=cls.BACKGROUND,
            foreground=cls.TEXT_PRIMARY,
            fieldbackground=cls.BACKGROUND,
            rowheight=30,
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_MEDIUM)
        )
        
        # Configure the Treeview header style
        style.configure(
            "Treeview.Heading",  # Changed from Custom.Treeview.Heading
            background=cls.TABLE_HEADER_BG,
            foreground=cls.TABLE_HEADER_FG,
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_MEDIUM, "bold"),
            relief="flat"
        )
        
        # Map states for the Treeview header
        style.map("Treeview.Heading",
            background=[
                ("active", cls.PRIMARY),
                ("pressed", cls.PRIMARY),
            ],
            foreground=[
                ("active", "white"),
                ("pressed", "white"),
            ]
        )
        
        # Map states for the Treeview
        style.map("Custom.Treeview",
            background=[
                ("selected", cls.TABLE_ROW_SELECTED),
                ("!selected", cls.BACKGROUND)
            ],
            foreground=[
                ("selected", "white"),
                ("!selected", cls.TEXT_PRIMARY)
            ]
        )
        
        # Configure Buttons
        style.configure(
            "Modern.TButton",
            background=cls.SECONDARY,
            foreground="white",
            padding=(20, 10),
            font=(cls.FONT_FAMILY, cls.FONT_SIZE_MEDIUM)
        )
        
        # Configure Progress bar
        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor=cls.BACKGROUND,
            background=cls.SECONDARY,
            thickness=10
        )

class ModernButton(tk.Button):
    def __init__(self, master, **kwargs):
        kwargs.setdefault('bg', ModernTheme.SECONDARY)  # Set default bg if not provided
        super().__init__(
            master,
            fg="white",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            **kwargs
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['background'] = "#2980B9"  # Darker shade of SECONDARY

    def on_leave(self, e):
        self['background'] = ModernTheme.SECONDARY

class DeleteButton(ModernButton):
    def __init__(self, master, **kwargs):
        kwargs['bg'] = ModernTheme.ACCENT  # Set bg in kwargs instead of passing directly
        super().__init__(master, **kwargs)

    def on_enter(self, e):
        self['background'] = "#C0392B"  # Darker shade of ACCENT

    def on_leave(self, e):
        self['background'] = ModernTheme.ACCENT

class RecordLogParser:
    @staticmethod
    def parse_log_file(log_path):
        flights = []
        current_flight = None
        line_number = 0
        
        print(f"\n=== Starting to parse log file: {log_path} ===")
        
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    line_number += 1
                    line = line.strip()
                    
                    # Debug output for every 1000 lines
                    if line_number % 1000 == 0:
                        print(f"Processing line {line_number}")
                    
                    # Check for new flight entry
                    if line.startswith('[') and line.endswith('.000]'):
                        print(f"\nFound potential flight entry at line {line_number}: {line}")
                        
                        # Extract flight info from path
                        flight_path = line[1:-1] 
                        dir_name = os.path.dirname(flight_path)
                        file_name = os.path.basename(flight_path)
                        
                        # Parse flight details
                        match = re.match(r'(\d{2})(\d{2})(\d{2})_(\d{3})\.000', file_name)
                        if match:
                            day, month, year, plane = match.groups()
                            
                            current_flight = {
                                'date': f'20{year}{month}{day}',
                                'plane_number': plane,
                                'base_path': dir_name,
                                'base_filename': file_name[:-4],  
                                'size': 0,
                                'start_time': None,
                                'end_time': None
                            }
                            print(f"Successfully parsed flight details: {current_flight}")
                        else:
                            print(f"Warning: Could not parse flight details from filename: {file_name}")
                    
                    # Get start time
                    elif line.startswith('StartedAt=') and current_flight:
                        time_str = line.split('=')[1]
                        current_flight['start_time'] = time_str
                        print(f"Found start time: {time_str}")
                    
                    # Get end time and add flight to list
                    elif line.startswith('FinishedAt=') and current_flight:
                        time_str = line.split('=')[1]
                        current_flight['end_time'] = time_str
                        print(f"Found end time: {time_str}")
                        flights.append(current_flight)
                        print(f"Added flight to list. Total flights so far: {len(flights)}")
                        current_flight = None
                    
                    # Get data length
                    elif line.startswith('DataLength=') and current_flight:
                        try:
                            size_str = line.split('=')[1].split(':')[0]
                            current_flight['size'] = int(size_str)
                            print(f"Found data length: {size_str}")
                        except (IndexError, ValueError) as e:
                            print(f"Warning: Could not parse data length from line: {line}")
                            print(f"Error: {str(e)}")
                            current_flight['size'] = 0
        
        except Exception as e:
            print(f"\nError while parsing log file:")
            print(f"Last line processed: {line_number}")
            print(f"Error details: {str(e)}")
            import traceback
            print("Full traceback:")
            print(traceback.format_exc())
            return []
            
        print(f"\n=== Finished parsing log file ===")
        print(f"Total flights found: {len(flights)}")
        return flights

class DriveSelector(tk.Toplevel):
    def __init__(self, parent, drive_mapping):
        super().__init__(parent)
        self.title("Select Drives to Scan")
        self.geometry("500x600")
        self.configure(bg=ModernTheme.BACKGROUND)
        
        self.selected_drives = []
        self.drive_mapping = drive_mapping
        
        # Title Label with modern styling
        title_frame = tk.Frame(self, bg=ModernTheme.PRIMARY, pady=15)
        title_frame.pack(fill="x")
        
        tk.Label(
            title_frame,
            text="Select Drives to Scan",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_LARGE, "bold"),
            fg="white",
            bg=ModernTheme.PRIMARY
        ).pack()
        
        # Main content frame
        content_frame = tk.Frame(self, bg=ModernTheme.BACKGROUND, pady=20)
        content_frame.pack(fill="both", expand=True, padx=30)
        
        self.check_vars = {}
        
        # Create checkbuttons with modern styling
        for drive_path, drive_id in sorted(drive_mapping.items(), key=lambda x: x[1]):
            var = tk.BooleanVar()
            self.check_vars[drive_path] = var
            
            frame = tk.Frame(content_frame, bg=ModernTheme.BACKGROUND, pady=5)
            frame.pack(fill="x")
            
            cb = ttk.Checkbutton(
                frame,
                text=f"Drive ID {drive_id}",
                variable=var,
                style="Modern.TCheckbutton"
            )
            cb.pack(side="left")
            
            tk.Label(
                frame,
                text=f"({drive_path})",
                font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_SMALL),
                fg=ModernTheme.TEXT_SECONDARY,
                bg=ModernTheme.BACKGROUND
            ).pack(side="left", padx=5)
        
        # Button frame
        btn_frame = tk.Frame(self, bg=ModernTheme.BACKGROUND, pady=20)
        btn_frame.pack(fill="x", padx=30)
        
        ModernButton(
            btn_frame,
            text="Select All",
            command=self.select_all
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame,
            text="Clear All",
            command=self.clear_all
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame,
            text="Scan Selected",
            command=self.confirm
        ).pack(side="right", padx=5)
        
        self.transient(parent)
        self.grab_set()

    def select_all(self):
        for var in self.check_vars.values():
            var.set(True)
    
    def clear_all(self):
        for var in self.check_vars.values():
            var.set(False)
    
    def confirm(self):
        self.selected_drives = [
            drive for drive, var in self.check_vars.items() 
            if var.get()
        ]
        self.destroy()

class FlightFileManager:
    def __init__(self, root):
        self.root = root
        self.drive_mapping = {
            "C:/": 61, "Y:/": 62, "X:/": 63, "W:/": 64,
            "V:/": 65, "U:/": 66, "T:/": 67,
        }
        self.flight_data = {}
        self.executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 1)
        
        # Configure modern theme
        ModernTheme.configure_styles()
        self.init_gui()

    def init_gui(self):
        self.root.title("Flight File Manager")
        self.root.geometry("1200x800")
        self.root.configure(bg=ModernTheme.BACKGROUND)
        
        # Title bar
        title_frame = tk.Frame(self.root, bg=ModernTheme.PRIMARY, pady=15)
        title_frame.pack(fill="x")
        
        tk.Label(
            title_frame,
            text="Flight File Manager",
            font=(ModernTheme.FONT_FAMILY, int(ModernTheme.FONT_SIZE_LARGE * 1.5), "bold"),
            fg="white",
            bg=ModernTheme.PRIMARY
        ).pack()
        
        # Menu Bar with modern styling
        menubar = tk.Menu(self.root, bg=ModernTheme.PRIMARY, fg="white")
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg=ModernTheme.BACKGROUND, fg=ModernTheme.TEXT_PRIMARY)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Drives & Scan", command=self.show_drive_selector)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Main content frame
        content_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Treeview with modern styling
        # Treeview with modern styling
        self.table = ttk.Treeview(
            content_frame,
            columns=("date", "plane", "id", "start_time", "end_time", "size"),
            show='headings',
            style="Custom.Treeview"
        )
        
        # Override default style for headers
        self.table.tag_configure('header', background=ModernTheme.TABLE_HEADER_BG, foreground="white")
        
        # Configure columns
        column_config = {
            "date": ("Date", 120),
            "plane": ("Aircraft", 100),
            "id": ("Drive ID", 80),
            "start_time": ("Start Time", 150),
            "end_time": ("End Time", 150),
            "size": ("Size", 100)
        }
        
        for col, (heading, width) in column_config.items():
            self.table.heading(col, text=heading, anchor="center")
            self.table.column(col, width=width, anchor="center")

        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.table.yview)
        x_scrollbar = ttk.Scrollbar(content_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Grid layout for table and scrollbars
        self.table.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Button frame with modern styling
        btn_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ModernButton(
            btn_frame,
            text="Copy Selected",
            command=self.copy_files
        ).pack(side="right", padx=5)
        
        DeleteButton(
            btn_frame,
            text="Delete Selected",
            command=self.delete_files
        ).pack(side="right", padx=5)
        
        ModernButton(
            btn_frame,
            text="Easter Egg",
            command=self.display_easter_egg
        ).pack(side="left", padx=5)
        
        # Status frame
        status_frame = tk.Frame(self.root, bg=ModernTheme.BACKGROUND)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            maximum=100,
            style="Modern.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x", pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_MEDIUM),
            fg=ModernTheme.TEXT_SECONDARY,
            bg=ModernTheme.BACKGROUND
        )
        self.status_label.pack(pady=5)

    def show_drive_selector(self):
        selector = DriveSelector(self.root, self.drive_mapping)
        self.root.wait_window(selector)
        if selector.selected_drives:
            self.load_files(selector.selected_drives)

    def easter_egg_message(self):
        messages = [
            "Benjamin likes little boys :-(",
            "Kiril is giving that Hawk Tuah",
            "where is kush kush"
        ]
        return random.choice(messages)

    def display_easter_egg(self):
        messagebox.showinfo("Easter Egg", self.easter_egg_message())

    async def scan_record_logs(self, selected_drives):
        start_time = time.time()
        flight_data = {}

        for drive in selected_drives:
            # Try both the root directory and the expected subdirectory
            possible_paths = [
                Path(drive) / '!shu_fd' / 'das' / 'RECORDS.LOG',
                Path(drive) / '!shu_fd' / 'das' / 'RECORDS',  
            ]
            
            log_found = False
            for log_path in possible_paths:
                try:
                    if log_path.exists():
                        print(f"Found log file at: {log_path}")  # Debug 
                        flights = RecordLogParser.parse_log_file(str(log_path))
                        for flight in flights:
                            # Use the base_filename directly as the key
                            key = flight['base_filename']
                            flight_data[key] = {
                                'base_path': flight['base_path'],
                                'base_filename': flight['base_filename'],
                                'size': flight['size'],
                                'start_time': flight['start_time'],
                                'end_time': flight['end_time'],
                                'drive': drive
                            }
                        log_found = True
                        print(f"Successfully processed {len(flights)} flights from {log_path}")  # Debug print
                        break
                except Exception as e:
                    print(f"Error processing log file {log_path}: {str(e)}")
            
            if not log_found:
                print(f"No valid RECORD.LOG found in any of the expected locations for drive {drive}")

        end_time = time.time()
        print(f"Log scan completed in {end_time - start_time:.2f} seconds")
        return flight_data

    def load_files(self, selected_drives):
        self.status_label.config(text="Loading files...")
        self.progress_var.set(0)
        self.table.delete(*self.table.get_children())
        
        async def process_logs():
            self.flight_data = await self.scan_record_logs(selected_drives)
            self.root.after(0, self.display_flights)

        asyncio.run(process_logs())

    def display_flights(self):
        for key, data in self.flight_data.items():
            # Parse the key directly
            match = re.match(r'(\d{6})_(\d{3})', key)
            if match:
                date_part, plane_number = match.groups()
                # Convert to DD/MM/YY format
                formatted_date = f"{date_part[0:2]}/{date_part[2:4]}/20{date_part[4:6]}"
                size_gb = data['size'] / (1024 * 1024 * 1024)
                
                self.table.insert("", "end", values=(
                    formatted_date,
                    plane_number,
                    self.drive_mapping.get(data['drive'], 'Unknown'),
                    data['start_time'],
                    data['end_time'],
                    f"{size_gb:.2f} GB"
                ))
        
        self.status_label.config(text="Ready")


    def get_flight_files(self, flight_key):
        """
        Get all related files for a given flight key.
        
        Args:
        flight_key (str): Full key with format 'DDMMYYYY_PlaneNumber_StationID'
        
        Returns:
        List of Path objects for matching files
        """
        try:
            # Split the full key and extract just the date and plane number
            # Example: '27112024_200_61' -> '271124_200'
            parts = flight_key.split('_')
            if len(parts) < 2:
                print(f"Invalid flight key format: {flight_key}")
                return []
            
            # Format date from DDMMYYYY to DDMMYY
            date_formatted = parts[0][0:2] + parts[0][2:4] + parts[0][6:8]
            simplified_key = f"{date_formatted}_{parts[1]}"
            
            # Construct the base path
            base_path = Path("C:/!shu_fd/das")
            
            # Verbose logging to help diagnose issues
            print(f"Searching for files:")
            print(f"Original flight key: {flight_key}")
            print(f"Simplified search key: {simplified_key}")
            print(f"Base path: {base_path}")
            
            # Use glob to find files that start with the simplified key
            matching_files = list(base_path.glob(f"{simplified_key}*"))
            
            print(f"Found {len(matching_files)} matching files:")
            for file in matching_files:
                print(f" - {file}")
            
            return matching_files
        
        except Exception as e:
            print(f"Error in get_flight_files: {str(e)}")
            return []


    def copy_files(self):
        """
        Copy selected flight files to a chosen destination directory.
        """
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to copy.")
            return
        
        dest_dir = filedialog.askdirectory(title="Select Destination")
        if not dest_dir:
            return
            
        dest_path = Path(dest_dir)
        total_files = 0
        copied_files = 0
        
        self.status_label.config(text="Copying files...")
        self.progress_var.set(0)
        
        def copy_task():
            nonlocal total_files, copied_files
            
            try:
                # First pass: count total files
                for item in selected:
                    values = self.table.item(item, 'values')
                    if values:
                        date = values[0].replace("/", "")  # Convert DD/MM/YYYY to DDMMYYYY
                        plane_number = values[1]
                        drive_id = values[2]
                        key = f"{date}_{plane_number}_{drive_id}"
                        
                        files = self.get_flight_files(key)
                        total_files += len(files)
                
                # Second pass: copy files
                for item in selected:
                    values = self.table.item(item, 'values')
                    if values:
                        date = values[0].replace("/", "")
                        plane_number = values[1]
                        drive_id = values[2]
                        key = f"{date}_{plane_number}_{drive_id}"
                        
                        files = self.get_flight_files(key)
                        for file in files:
                            try:
                                shutil.copy2(file, dest_path / file.name)
                                copied_files += 1
                                progress = (copied_files / total_files) * 100
                                self.root.after(0, self.progress_var.set, progress)
                                self.root.after(0, self.status_label.config, 
                                              {"text": f"Copying files... ({copied_files}/{total_files})"})
                            except Exception as e:
                                print(f"Error copying {file}: {str(e)}")
                                self.root.after(0, messagebox.showerror, "Copy Error", 
                                              f"Error copying file {file}: {str(e)}")
                
                self.root.after(0, messagebox.showinfo, "Copy Complete", 
                              f"Successfully copied {copied_files} out of {total_files} files.")
            finally:
                self.root.after(0, self.status_label.config, {"text": "Ready"})
                self.root.after(0, self.progress_var.set, 0)
        
        self.executor.submit(copy_task)

    def delete_files(self):
        """
        Delete selected flight files.
        """
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to delete.")
            return
        
        # Count total files before asking for confirmation
        total_files = 0
        for item in selected:
            values = self.table.item(item, 'values')
            if values:
                date = values[0].replace("/", "")
                plane_number = values[1]
                drive_id = values[2]
                key = f"{date}_{plane_number}_{drive_id}"
                files = self.get_flight_files(key)
                total_files += len(files)
        
        confirm = messagebox.askyesno("Confirm Deletion", 
                                    f"Are you sure you want to delete {total_files} files?")
        if not confirm:
            return
        
        self.status_label.config(text="Deleting files...")
        self.progress_var.set(0)
        deleted_files = 0
        
        def delete_task():
            nonlocal deleted_files
            
            try:
                for item in selected:
                    values = self.table.item(item, 'values')
                    if values:
                        date = values[0].replace("/", "")
                        plane_number = values[1]
                        drive_id = values[2]
                        key = f"{date}_{plane_number}_{drive_id}"
                        
                        files = self.get_flight_files(key)
                        for file in files:
                            try:
                                os.remove(file)
                                deleted_files += 1
                                progress = (deleted_files / total_files) * 100
                                self.root.after(0, self.progress_var.set, progress)
                                self.root.after(0, self.status_label.config, 
                                              {"text": f"Deleting files... ({deleted_files}/{total_files})"})
                            except Exception as e:
                                print(f"Error deleting {file}: {str(e)}")
                                self.root.after(0, messagebox.showerror, "Deletion Error", 
                                              f"Error deleting file {file}: {str(e)}")
                
                # Remove deleted items from the table
                for item in selected:
                    self.table.delete(item)
                
                self.root.after(0, messagebox.showinfo, "Deletion Complete", 
                              f"Successfully deleted {deleted_files} out of {total_files} files.")
            finally:
                self.root.after(0, self.status_label.config, {"text": "Ready"})
                self.root.after(0, self.progress_var.set, 0)
        
        self.executor.submit(delete_task)

if __name__ == "__main__":
    root = tk.Tk()
    app = FlightFileManager(root)
    root.mainloop()
