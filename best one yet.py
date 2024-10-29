import os
import random
import shutil
import re
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, font
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import asyncio
import time

class DriveSelector(tk.Toplevel):
    def __init__(self, parent, drive_mapping):
        super().__init__(parent)
        self.title("Select Drives to Scan")
        self.geometry("400x500")
        
        self.selected_drives = []
        self.drive_mapping = drive_mapping
        
        # Create and pack widgets
        tk.Label(self, text="Select drives to scan:", font=('Arial', 12)).pack(pady=10)
        
        # Create frame for checkbuttons
        self.check_frame = tk.Frame(self)
        self.check_frame.pack(fill="both", expand=True, padx=20)
        
        # Create variables to store checkbox states
        self.check_vars = {}
        
        # Create checkbuttons for each drive
        for drive_path, drive_id in sorted(drive_mapping.items(), key=lambda x: x[1]):
            var = tk.BooleanVar()
            self.check_vars[drive_path] = var
            cb = ttk.Checkbutton(
                self.check_frame, 
                text=f"Drive ID {drive_id} ({drive_path})", 
                variable=var
            )
            cb.pack(anchor="w", pady=5)
        
        # Buttons frame
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Scan Selected", command=self.confirm).pack(side="right", padx=5)
        
        # Make dialog modal
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
            "Z:/": 61, "Y:/": 62, "X:/": 63 , "W:/": 64,
            "V:/": 65, "U:/": 66, "T:/": 67,
        }
        self.flight_data = {}
        self.scan_complete = mp.Event()
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

        # Menu Bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Drives & Scan", command=self.show_drive_selector)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(fill="both", expand=True)
        
        self.table = ttk.Treeview(self.table_frame, columns=("date", "plane", "id", "files", "GB"), show='headings', style="Custom.Treeview")
        self.table.pack(fill="both", expand=True)

        for col in ("date", "plane", "id", "files", "GB"):
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

    async def scan_flight_records(self, selected_drives):
        pattern = re.compile(r'(\d{6})_(\d+)')
        total_drives = len(selected_drives)

        async def process_drive(drive):
            drive_data = []
            shu_fd_folder = Path(drive) / '!shu_fd'
            if shu_fd_folder.exists():
                for file in shu_fd_folder.rglob('das/*'):
                    if file.is_file() and pattern.match(file.stem):
                        match = pattern.match(file.stem)
                        if match:
                            date, plane_number = match.groups()
                            try:
                                size = file.stat().st_size
                            except OSError:
                                size = 0
                            drive_data.append({
                                "date": date,
                                "plane_number": plane_number,
                                "filepath": file,
                                "drive_id": self.drive_mapping.get(drive, "Unknown"),
                                "size": size
                            })
            return drive_data

        start_time = time.time()
        async with mp.Pool(processes=os.cpu_count()) as pool:
            results = await asyncio.gather(*[pool.apply_async(process_drive, args=(drive,)) for drive in selected_drives])

        flight_data = {}
        for drive_data in results:
            for entry in drive_data:
                key = f"{entry['date']}_{entry['plane_number']}_{entry['drive_id']}"
                if key not in flight_data:
                    flight_data[key] = {"files": [], "total_size": 0}
                flight_data[key]["files"].append(entry['filepath'])
                flight_data[key]["total_size"] += entry['size'] / (1024 * 1024 * 1024)

        end_time = time.time()
        print(f"Scan completed in {end_time - start_time:.2f} seconds")
        self.flight_data = flight_data
        self.scan_complete.set()

    def load_files(self, selected_drives):
        self.status_label.config(text="Loading files...")
        self.progress_var.set(0)
        self.table.delete(*self.table.get_children())
        self.scan_complete.clear()
        asyncio.create_task(self.scan_flight_records(selected_drives))
        self.root.after(100, self.check_scan_complete)

    def check_scan_complete(self):
        if self.scan_complete.is_set():
            self.display_flights()
        else:
            self.root.after(100, self.check_scan_complete)

    def display_flights(self):
        for key, data in self.flight_data.items():
            date, plane_number, drive_id = key.split('_')
            formatted_date = f"{date[:2]}/{date[2:4]}/{date[4:]}"
            total_size = round(data["total_size"], 2)
            self.table.insert("", "end", values=(formatted_date, plane_number, drive_id, f"{len(data['files'])} files", f"{total_size:.2f}"))
        self.status_label.config(text="Ready")


    def copy_files(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to copy.")
            return
        
        dest_dir = filedialog.askdirectory(title="Select Destination")
        if not dest_dir:
            return
        
        self.status_label.config(text="Copying files...")
        threading.Thread(target=self._copy_files, args=(selected, dest_dir), daemon=True).start()


    def _copy_files(self, selected, dest_dir):
        for item in selected:
            values = self.table.item(item, 'values')
            if values:
                date, plane_number, drive_id, _, _ = values
                unformatted_date = date.replace("/", "")
                key = f"{unformatted_date}_{plane_number}_{drive_id}"
                if key in self.flight_data:
                    for file in self.flight_data[key]["files"]:
                        try:
                            shutil.copy2(file, dest_dir)
                        except Exception as e:
                            self.root.after(0, messagebox.showerror, "Copy Error", f"Error copying file {file}: {str(e)}")
        self.root.after(0, messagebox.showinfo, "Copy Complete", "Selected files have been copied.")
        self.root.after(0, self.status_label.config, {"text": "Ready"})

    def delete_files(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to delete.")
            return
        
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected files?")
        if not confirm:
            return
        
        self.status_label.config(text="Deleting files...")
        threading.Thread(target=self._delete_files, args=(selected,), daemon=True).start()

    def _delete_files(self, selected):
        for item in selected:
            values = self.table.item(item, 'values')
            if values:
                date, plane_number, drive_id, _, _ = values
                unformatted_date = date.replace("/", "")
                key = f"{unformatted_date}_{plane_number}_{drive_id}"
                if key in self.flight_data:
                    for file in self.flight_data[key]["files"]:
                        try:
                            os.remove(file)
                        except Exception as e:
                            self.root.after(0, messagebox.showerror, "Deletion Error", f"Error deleting file {file}: {str(e)}")
        self.root.after(0, messagebox.showinfo, "Deletion Complete", "Selected files have been deleted.")
        self.root.after(0, self.status_label.config, {"text": "Ready"})

if __name__ == "__main__":
    root = tk.Tk()
    app = FlightFileManager(root)
    root.mainloop()