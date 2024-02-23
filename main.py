import heapq
import time
import threading
import os
import subprocess
import json

from datetime import datetime
from file_watcher import FileWatcher
from playlist_manager import PlaylistManager
from video_processing import create_video_from_snapshot, reencode_video
from streaming_server import start_streaming_server
from cleanup import cleanup_temp_files

def load_settings():
    with open('settings.json', 'r') as f:
        return json.load(f)

def main():
    settings = load_settings()
    watch_directory = settings['watch_directory']
    delay_minutes = settings['delay_minutes']
    stream_url = settings['stream_url']
    temp_directory = settings['temp_directory']
    duration = settings['duration']
    playlist_dir = settings['playlist_dir']
    placeholder_dir = settings['placeholder_dir']
    excluded_files = settings['excluded_files']

    file_watcher = FileWatcher(watch_directory, duration, delay_minutes, temp_directory)
    file_watcher.start()

    print(f"\n 1. Initializing Playlist Manager...")
    playlist_manager = PlaylistManager(playlist_dir, temp_directory, placeholder_dir, duration)
    playlist_manager.initialize_playlists()

    active_playlist = os.path.basename(playlist_manager.active_playlist)
    playlist_manager.current_index = 1
    print(f" 2. Made the playlist `{active_playlist}` active")
    print(" 3. Waiting for the first valid video file to be processed...")

    while not file_watcher.queue or file_watcher.queue[0][0] > datetime.now():
        time.sleep(1)

    if file_watcher.queue:
        _, first_file, file_type, *optional_duration = file_watcher.queue[0]
        if file_type == 'snapshot':
            if first_file in file_watcher.processed_files:
                print("")
            else:
                adjusted_duration = optional_duration[0] if optional_duration else duration
                video_file = create_video_from_snapshot(first_file, adjusted_duration, temp_directory)
                file_watcher.mark_processed(first_file)
                time.sleep(1)
        elif file_type == 'recording':
            actual_duration = file_watcher.get_video_duration(first_file)

            reencoded_file = reencode_video(first_file, temp_directory, actual_duration)
            file_watcher.mark_processed(first_file)

            video_file = reencoded_file  
            adjusted_duration = actual_duration

        time.sleep(1)
        playlist_manager.add_video_to_playlist(video_file, adjusted_duration)

    playlist_manager_thread = threading.Thread(target=playlist_manager.run)
    playlist_manager_thread.start()

    playlist_manager.current_index = 0
    print(f" 4. Made the playlist `{active_playlist}` active")

    playlist_manager.finished_processing_first_video()

    ffmpeg_process = start_streaming_server(playlist_manager.active_playlist, stream_url)
    print(f" 5. Started streaming rtsp feed with stream URL: {stream_url}")

    print("\n --------- YOUR STREAM IS NOW UP AND RUNNING ---------\n")

    try:
        while True:
            while file_watcher.queue and file_watcher.queue[0][0] <= datetime.now():
                scheduled_time, next_file, file_type, *optional_duration = heapq.heappop(file_watcher.queue)
                file_watcher.print_queue()
                if file_type == 'snapshot':
                    if next_file in file_watcher.processed_files:
                        continue  
                    adjusted_duration = optional_duration[0] if optional_duration else duration
                    print(f"  **MAIN SCRIPT** Adjusted Duration ({adjusted_duration}) = Optional Duration ({optional_duration[0] if optional_duration else 'None'}) if {optional_duration} else {duration}\n")
                    next_file = create_video_from_snapshot(next_file, adjusted_duration, temp_directory)
                    file_watcher.mark_processed(next_file)
                elif file_type == 'recording':
                    actual_duration = file_watcher.get_video_duration(next_file)

                    reencoded_file = reencode_video(next_file, temp_directory, actual_duration)
                    file_watcher.mark_processed(next_file)

                    next_file = reencoded_file  
                    adjusted_duration = actual_duration

                time.sleep(1)
                playlist_manager.add_video_to_playlist(next_file, adjusted_duration)
                print("")

            cleanup_temp_files(temp_directory, excluded_files, min_age_minutes=120)

            time.sleep(5)

            if ffmpeg_process.poll() is not None:
                print(f"FFmpeg process exited with code {ffmpeg_process.returncode}")
                with open('ffmpeg_streaming_log.txt', 'r') as log_file:
                    print(log_file.read())
                ffmpeg_process = restart_streaming_server(ffmpeg_process, playlist_manager, stream_url)

    except KeyboardInterrupt:
        file_watcher.stop()
        playlist_manager.stop()
        playlist_manager_thread.join()
        print("\nFile watcher and playlist manager stopped due to KeyboardInterrupt")

        print("  - Removing temp video files and playlists")
        for filename in os.listdir(temp_directory):
            file_path = os.path.join(temp_directory, filename)
            if (filename.endswith('.txt') or filename.endswith('.mp4')) and filename not in excluded_files:
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"  - Error removing temp video file {filename}: {e}")

def restart_streaming_server(ffmpeg_process, playlist_manager, stream_url):
    if ffmpeg_process:
        ffmpeg_process.terminate()
        try:
            ffmpeg_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            ffmpeg_process.kill()
            ffmpeg_process.wait()
    
    print("\nERROR - FFmpeg process has stopped. Attempting to restart...\n")
    return start_streaming_server(playlist_manager.active_playlist, stream_url)

if __name__ == "__main__":
    main()