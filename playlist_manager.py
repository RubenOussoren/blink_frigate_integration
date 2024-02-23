import os
import threading
import time

def is_file_ready(file_path):
    try:
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    except OSError as e:
        print(f"Error checking file readiness: {e}")
        return False

class PlaylistManager:
    def __init__(self, playlist_dir, temp_directory, placeholder_dir, placeholder_duration):
        self.playlist_dir = playlist_dir
        self.temp_directory = temp_directory
        self.placeholder_dir = placeholder_dir
        self.playlists = [os.path.join(playlist_dir, 'list_1.txt'), os.path.join(playlist_dir, 'list_2.txt')]
        self.current_index = 1  
        self.durations = [0, 0] 
        self.placeholder_duration = placeholder_duration
        self.lock = threading.Lock()
        self.running = True
        self.processing_first_video = True

    @property
    def active_playlist(self):
        return self.playlists[self.current_index]

    @property
    def non_active_playlist(self):
        return self.playlists[(self.current_index + 1) % 2]

    def initialize_playlists(self):
        for playlist in self.playlists:
            if not os.path.exists(playlist):
                with open(playlist, 'w') as f:
                    f.write("ffconcat version 1.0\n")

    def add_placeholder_to_playlist(self):
        placeholder_filename = os.path.basename(self.placeholder_dir)
        self.append_to_playlist(placeholder_filename)
        non_active_index = (self.current_index + 1) % 2
        self.durations[non_active_index] += self.placeholder_duration 

    def run(self):
        self.initialize_playlists()
        last_check_time = time.time()
        placeholder_added = True
        while self.running:
            with self.lock:
                current_time = time.time()
                elapsed_time = current_time - last_check_time
                last_check_time = current_time

                if not self.processing_first_video:
                    self.durations[self.current_index] -= elapsed_time

                    if self.durations[self.current_index] <= 0 and not placeholder_added:
                        if self.should_add_placeholder():
                            self.add_placeholder_to_playlist()
                            placeholder_added = True

                    if self.durations[self.current_index] <= 0:
                        self.log_playlist_switch()
                        self.current_index = (self.current_index + 1) % 2
                        self.durations[(self.current_index + 1) % 2] = 0
                        minutes, seconds = divmod(self.durations[self.current_index], 60)
                        print(f" --- Switched from playlist {os.path.basename(self.non_active_playlist)} to playlist {os.path.basename(self.active_playlist)} with duration of {minutes} min {seconds} sec ---\n")
                        with open(self.non_active_playlist, 'w') as f:
                            f.write("ffconcat version 1.0\n")
                        self.durations[(self.current_index + 1) % 2] = 0
                        placeholder_added = False
                        # self.log_playlist_state()

            time.sleep(1)

    def finished_processing_first_video(self):
        with self.lock:
            self.processing_first_video = False

    def should_add_placeholder(self):
        active_playlist_empty = self.is_playlist_empty(self.active_playlist)
        non_active_playlist_empty = self.is_playlist_empty(self.non_active_playlist)
        return active_playlist_empty and non_active_playlist_empty

    def is_playlist_empty(self, playlist_path):
        with open(playlist_path, 'r') as f:
            lines = f.readlines()
        
        content_lines = [line for line in lines[1:] if not line.strip().startswith('file \'list_')]
        
        return len(content_lines) == 0

    def log_playlist_state(self):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        with open('playlist_log.txt', 'w') as log_file:
            log_file.write(f"Time: {current_time}\n")
            for i, playlist in enumerate(self.playlists):
                log_file.write(f"Playlist {i+1} ({'Active' if i == self.current_index else 'Non-Active'}):\n")
                with open(playlist, 'r') as playlist_file:
                    contents = playlist_file.read()
                    log_file.write(contents)
                log_file.write(f"Total Duration: {self.durations[i]:.2f} seconds\n\n")
            log_file.write("--------------------------------------------------\n\n")

    def log_playlist_switch(self):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        with open('playlist_log.txt', 'a') as log_file:
            log_file.write(f"Time: {current_time}\n")
            log_file.write(f"--- Switching from playlist {os.path.basename(self.non_active_playlist)} to playlist {os.path.basename(self.active_playlist)} ---\n\n")

    def append_to_playlist(self, video_filename):
        video_path = os.path.join(self.temp_directory, video_filename)
        if not is_file_ready(video_path):
            print(f"Warning: File {video_filename} is not ready to be added to the playlist.")
            return False
        
        non_active_playlist = self.non_active_playlist
        active_playlist_name = os.path.basename(self.active_playlist)

        with open(non_active_playlist, 'r') as f:
            lines = f.readlines()
        if lines and lines[-1].strip() == f"file '{active_playlist_name}'":
            lines = lines[:-1]
        with open(non_active_playlist, 'w') as f:
            f.writelines(lines)
            f.write(f"file '{video_filename}'\n")
            f.write(f"file '{active_playlist_name}'\n")
        
        # self.log_playlist_state()
        return True

    def add_video_to_playlist(self, video_path, video_duration):
        with self.lock:
            video_filename = os.path.basename(video_path)
            if self.append_to_playlist(video_filename):
                non_active_index = (self.current_index + 1) % 2
                self.durations[non_active_index] += video_duration
                minutes, seconds = divmod(video_duration, 60)
                total_min, total_sec = divmod(self.durations[non_active_index],60)
                print(f"  - Added video to {os.path.basename(self.non_active_playlist)} playlist: {os.path.basename(video_filename)} with duration of {minutes} min {seconds} sec")
                print(f"  - Total playlist duration is now {total_min} min {total_sec} sec")
            else:
                print(f"  - Skipped adding video to playlist: {os.path.basename(video_filename)} because the file is not ready.")

            # self.log_playlist_state()

    def stop(self):
        self.running = False