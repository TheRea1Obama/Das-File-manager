import os
import random
import re
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

class FlightFileManager:
    def __init__(self, root, network_drives):
        self.root = root
        self.network_drives = network_drives
        self.flight_data = []
        self.drive_mapping = {
            "C:/": 61,
            "Y:/": 62,
        }
        self.init_gui()
    
    def init_gui(self):
        self.root.title("Flight File Manager by Danny Karp")
        
        self.root.geometry("800x600")   

        self.root.resizable(True, True)
        
        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(fill="both", expand=True)
        
        self.table = tk.Listbox(self.table_frame, selectmode="extended")
        self.table.pack(fill="both", expand=True)

        x_scrollbar = tk.Scrollbar(self.table_frame, orient="horizontal", command=self.table.xview)
        x_scrollbar.pack(side="bottom", fill="x")
        y_scrollbar = tk.Scrollbar(self.table_frame, orient="vertical", command=self.table.yview)
        y_scrollbar.pack(side="right", fill="y")
        
        self.table.config(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)

        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(fill="x")
        
        self.copy_btn = tk.Button(self.btn_frame, text="Copy", command=self.copy_files)
        self.copy_btn.pack(side="left")
        
        self.delete_btn = tk.Button(self.btn_frame, text="Delete", command=self.delete_files)
        self.delete_btn.pack(side="right")
        
        self.easter_egg_btn = tk.Button(self.btn_frame, text="Easter Egg", command=self.display_easter_egg)
        self.easter_egg_btn.pack(side="bottom")
        
        self.load_files()

    def easter_egg_message(self):
        messages = [
            "Benjamin likes little boys :(",
            "This is a funny easter egg!",
            "Kiril is giving that Hawk Tuah and spiting on that thing!",
            "All my homies hate Kiril!",
            "Why is 6 afraid of 7? Because 7 8 9! \n kill me!"
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
            das_folder = Path(drive) / 'das'
            if das_folder.exists():
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
        self.table.delete(0, tk.END)
        for flight, files in self.flight_data.items():
            date, plane_number, drive_id = flight.split('_')
            self.table.insert(tk.END, f" {date}_{plane_number} (ID: {drive_id}): {len(files)} files")
    
    def copy_files(self):
        selected = self.table.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to copy.")
            return
        
        dest_dir = filedialog.askdirectory(title="Select Destination")
        if not dest_dir:
            return
        
        for idx in selected:
            key = list(self.flight_data.keys())[idx]
            for file in self.flight_data[key]:
                os.system(f'copy "{file}" "{dest_dir}"')
        
        messagebox.showinfo("Copy Complete", "Selected files have been copied.")
    
    def delete_files(self):
        selected = self.table.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a flight to delete.")
            return
        
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected files?")
        if not confirm:
            return
        
        for idx in selected:
            key = list(self.flight_data.keys())[idx]
            for file in self.flight_data[key]:
                os.remove(file)
        
        self.load_files()
        messagebox.showinfo("Deletion Complete", "Selected files have been deleted.")

if __name__ == "__main__":
    network_drives = ["C:/"]  
    
    root = tk.Tk()
    app = FlightFileManager(root, network_drives)
    root.mainloop()
