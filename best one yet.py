import os
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

class RecordLogParser:
    @staticmethod
    def parse_log_file(log_path):
        flights = []
        current_flight = None
        
        with open(log_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Check for new flight entry
                if line.startswith('[') and line.endswith('.000]'):
                    # Extract flight info from path
                    flight_path = line[1:-1] 
                    dir_name = os.path.dirname(flight_path)
                    file_name = os.path.basename(flight_path)
                    
                    # Parse flight details
                    match = re.match(r'(\d{2})(\d{2})(\d{2})_(\d+)\.000', file_name)
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
                
                # Get start time
                elif line.startswith('StartedAt=') and current_flight:
                    time_str = line.split('=')[1]
                    current_flight['start_time'] = time_str
                
                # Get end time and add flight to list
                elif line.startswith('FinishedAt=') and current_flight:
                    time_str = line.split('=')[1]
                    current_flight['end_time'] = time_str
                    flights.append(current_flight)
                    current_flight = None
                
                # Get data length
                elif line.startswith('DataLength=') and current_flight:
                    try:
                        size_str = line.split('=')[1].split(':')[0]
                        current_flight['size'] = int(size_str)
                    except (IndexError, ValueError):
                        current_flight['size'] = 0
        
        return flights

class DriveSelector(tk.Toplevel):
    def __init__(self, parent, drive_mapping):
        super().__init__(parent)
        self.title("Select Drives to Scan")
        self.geometry("400x500")
        
        self.selected_drives = []
        self.drive_mapping = drive_mapping
        
        tk.Label(self, text="Select drives to scan:", font=('Arial', 12)).pack(pady=10)
        
        self.check_frame = tk.Frame(self)
        self.check_frame.pack(fill="both", expand=True, padx=20)
        
        self.check_vars = {}
        
        for drive_path, drive_id in sorted(drive_mapping.items(), key=lambda x: x[1]):
            var = tk.BooleanVar()
            self.check_vars[drive_path] = var
            cb = ttk.Checkbutton(
                self.check_frame, 
                text=f"Drive ID {drive_id} ({drive_path})", 
                variable=var
            )
            cb.pack(anchor="w", pady=5)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Scan Selected", command=self.confirm).pack(side="right", padx=5)
        
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
        self.init_gui()

    def init_gui(self):
        self.root.title("Flight File Manager by Danny Karp")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        custom_font = font.Font(size=14)

        style = ttk.Style()
        style.configure("Custom.Treeview", font=custom_font)
        style.configure("Custom.Treeview.Heading", font=custom_font)

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Drives & Scan", command=self.show_drive_selector)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(fill="both", expand=True)
        
        self.table = ttk.Treeview(
            self.table_frame,
            columns=("date", "plane", "id", "start_time", "end_time", "size"),
            show='headings',
            style="Custom.Treeview"
        )
        self.table.pack(fill="both", expand=True)

        for col in ("date", "plane", "id", "start_time", "end_time", "size"):
            self.table.heading(col, text=col.capitalize())
            self.table.column(col, width=100, anchor="center")

        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(fill="x")

        self.copy_btn = tk.Button(self.btn_frame, text="Copy", command=self.copy_files)
        self.copy_btn.pack(side="right", padx=5, pady=5)

        self.delete_btn = tk.Button(self.btn_frame, text="Delete", command=self.delete_files)
        self.delete_btn.pack(side="right", padx=5, pady=5)

        self.easter_egg_btn = tk.Button(self.btn_frame, text="Easter Egg", command=self.display_easter_egg)
        self.easter_egg_btn.pack(side="left", padx=5, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        
        self.status_label = tk.Label(self.root, text="Ready")
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
            log_path = Path(drive) / '!shu_fd' / 'das' / 'RECORD.LOG'
            if log_path.exists():
                try:
                    flights = RecordLogParser.parse_log_file(str(log_path))
                    for flight in flights:
                        key = f"{flight['date']}_{flight['plane_number']}_{self.drive_mapping.get(drive, 'Unknown')}"
                        flight_data[key] = {
                            'base_path': flight['base_path'],
                            'base_filename': flight['base_filename'],
                            'size': flight['size'],
                            'start_time': flight['start_time'],
                            'end_time': flight['end_time'],
                            'drive': drive
                        }
                except Exception as e:
                    print(f"Error processing log file {log_path}: {e}")

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
            date, plane_number, drive_id = key.split('_')
            formatted_date = f"{date[6:8]}/{date[4:6]}/{date[:4]}"
            size_gb = data['size'] / (1024 * 1024 * 1024)
            
            self.table.insert("", "end", values=(
                formatted_date,
                plane_number,
                drive_id,
                data['start_time'],
                data['end_time'],
                f"{size_gb:.2f} GB"
            ))
            
        self.status_label.config(text="Ready")

    def get_flight_files(self, flight_key):
        if flight_key not in self.flight_data:
            return []
            
        flight = self.flight_data[flight_key]
        base_path = Path(flight['drive']) / '!shu_fd' / 'das'
        pattern = f"{flight['base_filename']}.*"
        
        return list(base_path.glob(pattern))

    def copy_files(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to copy.")
            return
        
        dest_dir = filedialog.askdirectory(title="Select Destination")
        if not dest_dir:
            return
        
        self.status_label.config(text="Copying files...")
        
        def copy_task():
            for item in selected:
                values = self.table.item(item, 'values')
                if values:
                    date, plane_number, drive_id = values[:3]
                    date = date.replace("/", "")
                    key = f"{date}_{plane_number}_{drive_id}"
                    
                    files = self.get_flight_files(key)
                    for file in files:
                        try:
                            shutil.copy2(file, dest_dir)
                        except Exception as e:
                            self.root.after(0, messagebox.showerror, "Copy Error", 
                                          f"Error copying file {file}: {str(e)}")
                            
            self.root.after(0, messagebox.showinfo, "Copy Complete", 
                          "Selected files have been copied.")
            self.root.after(0, self.status_label.config, {"text": "Ready"})
        
        self.executor.submit(copy_task)

    def delete_files(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to delete.")
            return
        
        confirm = messagebox.askyesno("Confirm Deletion", 
                                    "Are you sure you want to delete the selected files?")
        if not confirm:
            return
        
        self.status_label.config(text="Deleting files...")
        
        def delete_task():
            for item in selected:
                values = self.table.item(item, 'values')
                if values:
                    date, plane_number, drive_id = values[:3]
                    date = date.replace("/", "")
                    key = f"{date}_{plane_number}_{drive_id}"
                    
                    files = self.get_flight_files(key)
                    for file in files:
                        try:
                            os.remove(file)
                        except Exception as e:
                            self.root.after(0, messagebox.showerror, "Deletion Error", 
                                          f"Error deleting file {file}: {str(e)}")
                            
            self.root.after(0, messagebox.showinfo, "Deletion Complete", 
                          "Selected files have been deleted.")
            self.root.after(0, self.status_label.config, {"text": "Ready"})
        
        self.executor.submit(delete_task)

if __name__ == "__main__":
    root = tk.Tk()
    app = FlightFileManager(root)
    root.mainloop()