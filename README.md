# Blink Camera Stream Automation

This Python project automates the process of monitoring a specified directory for new video snapshots or recordings from Blink cameras, processing these files, and dynamically managing and streaming a playlist of these videos. It's designed to work with a local file system where the Blink camera system saves snapshots and recordings. The project consists of several key components that work together to provide a seamless streaming experience.

## Features

- **File Watching**: Monitors a specified directory for new snapshots or recordings, adding them to a processing queue.
- **Video Processing**: Converts snapshots to videos and re-encodes recordings as needed, preparing them for streaming.
- **Playlist Management**: Dynamically manages a playlist, adding new videos and placeholders to ensure continuous streaming.
- **Streaming Server**: Utilizes FFmpeg to stream the managed playlist to a specified RTSP URL.
- **Cleanup**: Periodically cleans up old temporary video files to free up space.

## Components

- `main.py`: The entry point of the application, orchestrating the monitoring, processing, and streaming processes.
- `file_watcher.py`: Contains the `FileWatcher` class that watches for new files in the specified directory.
- `playlist_manager.py`: Manages the video playlist, including adding new videos and switching between active and non-active playlists.
- `video_processing.py`: Provides functions for creating videos from snapshots and re-encoding videos for streaming.
- `streaming_server.py`: Handles the streaming of the active playlist to the specified RTSP URL using FFmpeg.
- `cleanup.py`: Responsible for cleaning up old temporary files to maintain a clean working environment.

## Configuration

The application allows for external configuration of key parameters such as the directory to watch, streaming URL, temporary directory for processing, and more. These settings can be moved to a separate settings file (e.g., `settings.json`) for easy management and adjustment without altering the core script.

## Dependencies

- Python 3.x
- FFmpeg
- watchdog (for file monitoring)

## Setup and Usage

1. Ensure Python 3.x and FFmpeg are installed on your system.
2. Install the required Python packages: `pip install watchdog`.
3. Configure `settings.json` with your specific paths, URLs, and preferences.
4. Run the script: `python main.py`.

### Explanation of Settings Placeholders:
- **/path/to/watch/directory**: Replace with the directory path where new files from cameras are saved.
- **rtsp://your.stream.url:port/streamname**: Replace with your actual RTSP streaming URL.
- **/path/to/temporary/videos/directory**: Replace with the directory path for storing temporary video files.
- **/path/to/playlist/directory**: Replace with the directory path where playlists will be stored.
- **/path/to/placeholder/video.mp4**: Replace with the path to a placeholder video file to be used in the playlist.
- **example_excluded_file1.mp4, example_excluded_file2.mp4**: Replace with actual filenames you want to exclude from cleanup.
- **/path/to/ffmpeg/vaapi/device**: Replace with the device path used by FFmpeg for hardware acceleration, if applicable.

This project is ideal for users looking to automate the management and streaming of video files from Blink cameras, providing a flexible and configurable solution for home surveillance systems.