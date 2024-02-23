import os
from datetime import datetime

def cleanup_temp_files(temp_directory, excluded_files, min_age_minutes=120):
    current_time = datetime.now()
    files_to_remove = []

    for filename in os.listdir(temp_directory):
        file_path = os.path.join(temp_directory, filename)
        if os.path.isfile(file_path) and file_path.endswith('.mp4') and filename not in excluded_files:
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if (current_time - file_creation_time).total_seconds() > min_age_minutes * 60:
                files_to_remove.append(file_path)

    for file_path in files_to_remove:
        try:
            os.remove(file_path)
            print(f" - Removed old temporary file: {files_to_remove}\n")
        except OSError as e:
            print(f"  - Error removing file {files_to_remove}: {e}")