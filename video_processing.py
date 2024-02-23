import os
import subprocess
    
def create_video_from_snapshot(snapshot_path, duration, temp_directory):
    video_filename = os.path.basename(snapshot_path).replace('.jpg', '.mp4')
    output_path = os.path.join(temp_directory, video_filename)
    minutes, seconds = divmod(duration, 60)

    print(f" --------- Processing file: {os.path.basename(snapshot_path)} ---------")
    
    cmd = [
        'ffmpeg',
        # '-loglevel', 'debug',
        '-vaapi_device', '/dev/dri/renderD128',
        '-loop', '1',
        '-framerate', '24',  
        '-i', snapshot_path,
        '-f', 'lavfi',  
        '-i', 'anullsrc=channel_layout=mono:sample_rate=16000',  
        '-vf', 'format=nv12,hwupload,scale_vaapi=w=1280:h=720',
        '-c:v', 'h264_vaapi',
        '-profile:v', 'high', 
        '-level', '40',  
        '-r', '24', 
        '-g', '48', 
        '-bf', '0', 
        '-b:v', '2M',  
        '-t', str(duration),
        '-c:a', 'aac',  
        '-b:a', '32k',  
        '-ar', '16000',  
        '-ac', '1',  
        '-shortest',  
        '-movflags', '+faststart', 
        output_path
    ]
    with open('ffmpeg_snapshot_log.txt', 'w') as log_file:
        subprocess.run(cmd, check=True, stdout=log_file, stderr=log_file)

    print(f"  - Converted snapshot: {video_filename} with duration of {minutes} min {seconds} sec")

    return output_path 

def reencode_video(recording_path, temp_directory, actual_duration):
    video_filename = os.path.basename(recording_path)
    output_path = os.path.join(temp_directory, video_filename)
    minutes, seconds = divmod(actual_duration, 60)

    print(f" --------- Processing file: {video_filename} ---------")

    cmd = [
        'ffmpeg',
        # '-loglevel', 'debug',
        '-vaapi_device', '/dev/dri/renderD128',
        '-i', recording_path,
        '-vf', 'format=nv12,hwupload,scale_vaapi=w=1280:h=720',
        '-c:v', 'h264_vaapi',
        '-profile:v', 'high',
        '-level', '40',  
        '-r', '24',  
        '-g', '48', 
        '-bf', '0',  
        '-b:v', '2M', 
        '-c:a', 'aac',  
        '-b:a', '32k',  
        '-ar', '16000',  
        '-ac', '1',  
        '-movflags', '+faststart', 
        output_path
    ]
    with open('ffmpeg_reencode_log.txt', 'w') as log_file:
        subprocess.run(cmd, check=True, stdout=log_file, stderr=log_file)

    print(f"  - Re-encoded video: {video_filename} with duration of {minutes} min {seconds} sec")

    return output_path
