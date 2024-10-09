import os
import random
import shutil
import re
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, font, PhotoImage

class FlightFileManager:
    def __init__(self, root, network_drives):
        self.root = root
        self.network_drives = network_drives
        self.flight_data = []
        self.drive_mapping = {
            "C:/": 61,
            "E:/": 63,
            "Y:/": 62,
            "D:/": 64,
            "G:/": 65,
            "H:/": 66,
            "I:/": 67
        }
        self.init_gui()

    def init_gui(self):
        self.root.title("Flight File Manager by Danny Karp")
        self.root.geometry("800x600")   
        self.root.resizable(True, True)

        # self.plane_icon = PhotoImage(file="uav2.png")  

        custom_font = font.Font(size=14)

        style = ttk.Style()
        style.configure("Custom.Treeview", font=custom_font)
        style.configure("Custom.Treeview.Heading", font=custom_font)  

        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(fill="both", expand=True)
        
        self.table = ttk.Treeview(self.table_frame, columns=("date", "plane", "id", "files", "size"), show='headings', style="Custom.Treeview")
        self.table.pack(fill="both", expand=True)

        self.table.heading("date", text="Date")
        self.table.heading("plane", text="Plane")
        self.table.heading("id", text="ID")
        self.table.heading("files", text="Files")
        self.table.heading("size", text="GB")

        
        self.table.column("date", width=100, anchor="center")
        self.table.column("plane", width=100, anchor="center")
        self.table.column("id", width=50, anchor="center")
        self.table.column("files", width=100, anchor="center")
        self.table.column("size", width=50, anchor="center")


        # stupid scrollbars that doesnt work :( benjaming likes little boys :-(
        # x_scrollbar = tk.Scrollbar(self.table_frame, orient="horizontal", command=self.table.xview)
        # x_scrollbar.pack(side="bottom", fill="x")
        # y_scrollbar = tk.Scrollbar(self.table_frame, orient="vertical", command=self.table.yview)
        # y_scrollbar.pack(side="right", fill="y")
        
        # self.table.config(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)

        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(fill="x")

        self.copy_btn = tk.Button(self.btn_frame, text="Copy", command=self.copy_files)
        self.copy_btn.pack(side="right", padx=5, pady=5)

        self.delete_btn = tk.Button(self.btn_frame, text="Delete", command=self.delete_files)
        self.delete_btn.pack(side="right", padx=5, pady=5)

        self.copy_btn = tk.Button(self.btn_frame, text="reload", command=self.load_files)
        self.copy_btn.pack(side="right",padx=5, pady=5)

        self.easter_egg_btn = tk.Button(self.btn_frame, text="Easter Egg", command=self.display_easter_egg)
        self.easter_egg_btn.pack(side="left", padx=5, pady=5)
        
        self.load_files()

    def easter_egg_message(self):
        messages = [
            "Benjamin likes little boys :-(",
            "Kiril is giving that Hawk Tuah",
            "where is kush kush"
        ]
        return random.choice(messages)
    
    def show_about(self):
        messagebox.showinfo("About", "Flight File Manager\n\nCreated by Danny Karp")

    def display_easter_egg(self):
        messagebox.showinfo("Easter Egg", self.easter_egg_message())

    def load_files(self):
        self.flight_data = self.scan_flight_records()
        self.display_flights()

    def scan_flight_records(self):
        flight_data = []
        pattern = re.compile(r'(\d{6})_(\d+)')
        
        for drive in self.network_drives:
            # Focus the search within 'shu_fd' folder
            shu_fd_folder = Path(drive) / '!shu_fd'
            if shu_fd_folder.exists():
                for das_folder in shu_fd_folder.rglob('das'):
                    if das_folder.is_dir():
                        for file in das_folder.iterdir():
                            if file.is_file() and pattern.match(file.stem):
                                date, plane_number = pattern.match(file.stem).groups()
                                flight_data.append({
                                    "date": date,
                                    "plane_number": plane_number,
                                    "filepath": file,
                                    "drive_id": self.drive_mapping.get(drive, "Unknown") 
                                })
        
        grouped_data = {}

        for entry in flight_data:
            key = f"{entry['date']}_{entry['plane_number']}_{entry['drive_id']}"
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(entry['filepath'])
        
        return grouped_data

    def display_flights(self):
        self.table.delete(*self.table.get_children())  

        for key, data in self.flight_data.items():
            date, plane_number, drive_id = key.split('_')
            formated_date = f"{date[:2]}/{date[2:4]}/{date[4:]}"
            total_size = round(data["total_size"], 2)  # Round to 2 decimal places
            self.table.insert("", "end", values=(formated_date, plane_number, drive_id, f"{len(data['files'])} files", f"{total_size:.2f}"))

    def copy_files(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to copy.")
            return
        
        dest_dir = filedialog.askdirectory(title="Select Destination")
        if not dest_dir:
            return
        
        for item in selected:
            values = self.table.item(item, 'values')
            if values:
                date, plane_number, drive_id, _, _ = values

                unformatted_date = self.unformat_date(date)

                key = f"{unformatted_date}_{plane_number}_{drive_id}"
                if key in self.flight_data:
                    for file in self.flight_data[key]["files"]:
                        try:
                            shutil.copy2(file, dest_dir)
                        except Exception as e:
                            messagebox.showerror("Copy Error", f"Error copying file {file}: {str(e)}")
                else:
                    messagebox.showwarning("File Not Found", f"No files found for {key}")
        
        messagebox.showinfo("Copy Complete", "Selected files have been copied.")

    def delete_files(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to delete.")
            return
        
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected files?")
        if not confirm:
            return
        
        for item in selected:
            values = self.table.item(item, 'values')
            if values:
                date, plane_number, drive_id, _, _ = values

                unformatted_date = self.unformat_date(date)

                key = f"{unformatted_date}_{plane_number}_{drive_id}"

                if key in self.flight_data:
                    for file in self.flight_data[key]["files"]:
                        try:
                            os.remove(file)
                        except Exception as e:
                            messagebox.showerror("Deletion Error", f"Error deleting file {file}: {str(e)}")
                else:
                    messagebox.showwarning("File Not Found", f"No files found for {key}")
        
        self.load_files()
        messagebox.showinfo("Deletion Complete", "Selected files have been deleted.")


    def unformat_date(self,date):
        return date.replace("/", "")


if __name__ == "__main__":
    network_drives = ["C:/","D:/","E:/"]  
    
    root = tk.Tk()
    app = FlightFileManager(root, network_drives)
    root.mainloop()
