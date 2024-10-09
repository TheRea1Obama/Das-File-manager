# --------------------------------------------------------------------------------------------------   
# searching for it in a recursive way (takes alot more time)
def scan_flight_records(self):
        flight_data = []
        pattern = re.compile(r'(\d{6})_(\d+)')
        
        for drive in self.network_drives:
            
            for das_folder in Path(drive).rglob('das'):
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

# --------------------------------------------------------------------------------------------------   
# searching for it in only if the das folder is in the first directory
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

# --------------------------------------------------------------------------------------------------   
# searching for it in only if the shu_fd folder is in the first directory
def scan_flight_records(self):
    flight_data = []
    pattern = re.compile(r'(\d{6})_(\d+)')
    
    for drive in self.network_drives:
        # Focus the search within 'shu_fd' folder
        shu_fd_folder = Path(drive) / 'shu_fd'
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

# --------------------------------------------------------------------------------------------------   
# chat gpt magic it uses multiple cpu cores to speed up the process ----- but doesn't work

from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor

def process_drive(self, drive):
    flight_data = []
    pattern = re.compile(r'(\d{6})_(\d+)')
    
    shu_fd_folder = Path(drive) / 'shu_fd'
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
    return flight_data

def scan_flight_records(self):
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(self.process_drive, self.network_drives))

    flight_data = [item for sublist in results for item in sublist]

    grouped_data = {}
    for entry in flight_data:
        key = f"{entry['date']}_{entry['plane_number']}_{entry['drive_id']}"
        if key not in grouped_data:
            grouped_data[key] = []
        grouped_data[key].append(entry['filepath'])
    
    return grouped_data
