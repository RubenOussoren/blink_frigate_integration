import heapq
import os
import re
import subprocess
from datetime import datetime, timedelta
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class FileWatcher:
    def __init__(self, watch_directory, duration, delay_minutes, temp_directory):
        self.watch_directory = watch_directory
        self.duration = duration  
        self.time_left = duration
        self.delay_minutes = delay_minutes
        self.queue = []
        self.observer = Observer()
        self.event_handler = FileSystemEventHandler()
        self.event_handler.on_created = self.on_created
        self.temp_directory = temp_directory
        self.processed_files = set()

    def on_created(self, event):
        if not event.is_directory and os.path.isfile(event.src_path):
            print(f"  --------------------------------------------------------------")
            print(f"  --- Detected new file: {os.path.basename(event.src_path)} ---")
            if event.src_path.endswith(('.mp4', '.jpg')):
                timestamp = self.extract_timestamp(event.src_path)
                if timestamp:
                    file_type = 'recording' if event.src_path.endswith('.mp4') else 'snapshot'
                    heapq.heappush(self.queue, (timestamp, event.src_path, file_type))
                    self.reorder_and_adjust_queue(self.temp_directory) 
            else:
                print(f"  - File detected is neither a snapshot nor a recording, skipping: {os.path.basename(event.src_path)}")

    def mark_processed(self, file_path):
        self.processed_files.add(file_path)

    def reorder_and_adjust_queue(self, temp_directory):
        new_queue = []

        for item in sorted(self.queue):
            timestamp, file_path, file_type = item[:3]  
            adjusted_duration = item[3] if len(item) > 3 else None 

            if file_type == 'recording':
                print(f"  -RRR- Processing a Recording: {os.path.basename(file_path)} -RRR- ")
                recording_duration = self.get_video_duration(file_path)
                self.time_left -= recording_duration
                new_queue.append((timestamp, file_path, file_type))
                print(f"  - Recording ({os.path.basename(file_path)}) has a duration of {recording_duration}s. Duration for next snapshot is {self.time_left}s")
            elif file_type == 'snapshot':
                print(f"  -SSS- Processing a Snapshot: {os.path.basename(file_path)}, {self.time_left}s -SSS- ")
                video_filename = os.path.basename(file_path).replace('.jpg', '.mp4')
                video_path = os.path.join(temp_directory, video_filename)
                if os.path.exists(video_path):
                    continue

                if self.time_left <= 0:
                    self.time_left = self.duration
                    continue
                
                if adjusted_duration is None:
                    print ("")
                else:
                    print(f"  - Adjusted snapshot ({os.path.basename(file_path)}) duration from {adjusted_duration}s to {min(adjusted_duration, self.time_left)}s due to reduced time left")
                
                adjusted_duration = min(self.time_left, self.duration) if adjusted_duration is None else min(adjusted_duration, self.time_left)
                new_queue.append((timestamp, file_path, file_type, adjusted_duration))
                print(f"  --------------------------------------------------------------\n")
                self.time_left = self.duration

        self.queue = new_queue

    def get_video_duration(self, recording_path):
        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    recording_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            duration = float(result.stdout)
            return duration
        except ValueError as e:
            print(f" - Error parsing duration: {e}")
        except subprocess.CalledProcessError as e:
            print(f" - ffprobe error: {e.stderr}")
        return 0 

    def extract_timestamp(self, file_path):
        match = re.search(r'(\d{6})-Camera\d+-(Snapshot|Recording)\.(jpg|mp4)', os.path.basename(file_path))
        if match:
            time_str = match.group(1)
            path_components = file_path.split(os.sep)
            day_str = path_components[-2]
            month_str = path_components[-3]
            year_str = path_components[-4]
            
            timestamp_str = f"{year_str}/{month_str}/{day_str}/{time_str}"
            
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y/%m-%B/%d/%H%M%S')
                return timestamp
            except ValueError as e:
                print(f" - Error parsing timestamp: {e}")
        else:
            print(f" - No timestamp found in file name: {os.path.basename(file_path)}")
        return None
    
    def print_queue(self):
        print("  Current Queue:")
        for item in self.queue:
            scheduled_time, file_path, file_type = item[:3]
            optional_duration = item[3] if len(item) > 3 else "Default"
            print(f"    Scheduled Time: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                  f"File Path: {os.path.basename(file_path)}, "
                  f"File Type: {file_type}, "
                  f"Duration: {optional_duration}\n")

    def start(self):
        self.observer.schedule(self.event_handler, self.watch_directory, recursive=True)
        self.observer.start()
        self.scan_existing_files()

    def stop(self):
        self.observer.stop()
        self.observer.join()
        
    def scan_existing_files(self):
        now = datetime.now()
        delay_time = now - timedelta(minutes=self.delay_minutes)  
        today_path = os.path.join(
            self.watch_directory,
            'Snapshots',
            now.strftime('%Y/%m-%B/%d')
        )

        if not os.path.exists(today_path):
            return

        all_files = [f for f in os.listdir(today_path) if f.endswith(('.jpg', '.mp4'))]
        sorted_files = sorted(all_files)

        print("")

        for filename in sorted_files:
            file_path = os.path.join(today_path, filename)
            timestamp = self.extract_timestamp(file_path)
            if timestamp and delay_time <= timestamp <= now: 
                file_type = 'recording' if filename.endswith('.mp4') else 'snapshot'
                heapq.heappush(self.queue, (timestamp, file_path, file_type))
                print(f" - Added to queue: {os.path.basename(file_path)}")