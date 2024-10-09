import os
import random
import re
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, font
from concurrent.futures import ThreadPoolExecutor
import threading
import time

class FlightFileManager:
    def __init__(self, root, network_drives):
        self.root = root
        self.network_drives = network_drives
        self.flight_data = {}
        self.drive_mapping = {
            "C:/": 61, "E:/": 63, "Y:/": 62, "D:/": 64,
            "G:/": 65, "H:/": 66, "I:/": 67,
        }
        self.scan_complete = threading.Event()
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

        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(fill="both", expand=True)
        
        self.table = ttk.Treeview(self.table_frame, columns=("date", "plane", "id", "files", "size"), show='headings', style="Custom.Treeview")
        self.table.pack(fill="both", expand=True)

        for col in ("date", "plane", "id", "files", "size"):
            self.table.heading(col, text=col.capitalize())
            self.table.column(col, width=100, anchor="center")

        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(fill="x")

        self.copy_btn = tk.Button(self.btn_frame, text="Copy", command=self.copy_files)
        self.copy_btn.pack(side="right", padx=5, pady=5)

        self.delete_btn = tk.Button(self.btn_frame, text="Delete", command=self.delete_files)
        self.delete_btn.pack(side="right", padx=5, pady=5)

        self.reload_btn = tk.Button(self.btn_frame, text="Reload", command=self.load_files)
        self.reload_btn.pack(side="right", padx=5, pady=5)

        self.easter_egg_btn = tk.Button(self.btn_frame, text="Easter Egg", command=self.display_easter_egg)
        self.easter_egg_btn.pack(side="left", padx=5, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        
        self.status_label = tk.Label(self.root, text="Ready")
        self.status_label.pack(pady=5)

        self.root.after(100, self.load_files)

    def easter_egg_message(self):
        messages = [
            "Benjamin likes little boys :-(",
            "Kiril is giving that Hawk Tuah",
            "where is kush kush"
        ]
        return random.choice(messages)

    def display_easter_egg(self):
        messagebox.showinfo("Easter Egg", self.easter_egg_message())

    def load_files(self):
        self.status_label.config(text="Loading files...")
        self.progress_var.set(0)
        self.table.delete(*self.table.get_children())
        self.scan_complete.clear()
        threading.Thread(target=self.scan_flight_records, daemon=True).start()
        self.root.after(100, self.check_scan_complete)

    def check_scan_complete(self):
        if self.scan_complete.is_set():
            self.display_flights()
        else:
            self.root.after(100, self.check_scan_complete)

    def scan_flight_records(self):
        start_time = time.time()
        
        def process_drive(drive):
            drive_data = []
            records_log = Path(drive) / '!shu_fd' / 'RECORDS.LOG'
            if records_log.exists():
                with open(records_log, 'r') as f:
                    for line in f:
                        if line.startswith('[') and line.endswith(']\n'):
                            file_path = line.strip('[]').strip()
                            file_path = Path(file_path.replace('D:/', drive))
                            if file_path.exists():
                                match = re.search(r'(\d{6})_(\d+)', file_path.stem)
                                if match:
                                    date, plane_number = match.groups()
                                    size = file_path.stat().st_size
                                    drive_data.append({
                                        "date": date,
                                        "plane_number": plane_number,
                                        "filepath": file_path,
                                        "drive_id": self.drive_mapping.get(drive, "Unknown"),
                                        "size": size
                                    })
            return drive_data

        futures = [self.executor.submit(process_drive, drive) for drive in self.network_drives]

        flight_data = {}
        total_drives = len(self.network_drives)
        for i, future in enumerate(futures):
            for entry in future.result():
                key = f"{entry['date']}_{entry['plane_number']}_{entry['drive_id']}"
                if key not in flight_data:
                    flight_data[key] = {"files": [], "total_size": 0}
                flight_data[key]["files"].append(entry['filepath'])
                flight_data[key]["total_size"] += entry['size'] / (1024 * 1024 * 1024)  # Convert to GB
            self.progress_var.set((i + 1) / total_drives * 100)

        self.flight_data = flight_data
        end_time = time.time()
        print(f"Scan completed in {end_time - start_time:.2f} seconds")
        self.scan_complete.set()

    def display_flights(self):
        start_time = time.time()
        for key, data in self.flight_data.items():
            date, plane_number, drive_id = key.split('_')
            formatted_date = f"{date[:2]}/{date[2:4]}/{date[4:]}"
            total_size = round(data["total_size"], 2)
            self.table.insert("", "end", values=(formatted_date, plane_number, drive_id, f"{len(data['files'])} files", f"{total_size:.2f}"))
        end_time = time.time()
        print(f"Display completed in {end_time - start_time:.2f} seconds")
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
        self.root.after(0, self.load_files)
        self.root.after(0, messagebox.showinfo, "Deletion Complete", "Selected files have been deleted.")
        self.root.after(0, self.status_label.config, {"text": "Ready"})


if __name__ == "__main__":
    network_drives = ["C:/", "D:/", "E:/"]
    root = tk.Tk()
    app = FlightFileManager(root, network_drives)
    root.mainloop()
