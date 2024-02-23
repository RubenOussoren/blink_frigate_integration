import os
import subprocess

def start_streaming_server(playlist_path, stream_url):

    if not os.path.exists(playlist_path):
        raise RuntimeError(f"ERROR - Playlist file not found at {playlist_path}")

    cmd = [
        'ffmpeg',
        '-re',  
        '-f', 'concat',  
        '-safe', '0', 
        '-i', playlist_path, 
        '-c', 'copy',  
        '-rtsp_transport', 'tcp',  
        '-f', 'rtsp',  
        stream_url  
    ]
    with open('ffmpeg_streaming_log.txt', 'w') as log_file:
        process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
    return process