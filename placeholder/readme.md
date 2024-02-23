Command to create videos:
```
ffmpeg -vaapi_device /dev/dri/renderD128 -loop 1 -framerate 24 -i /home/roms/data/blink/live_stream_1/placeholder/images/unavailable_v2.png -f lavfi -i anullsrc=channel_layout=mono:sample_rate=16000 -vf "format=nv12,hwupload,scale_vaapi=w=1280:h=720" -c:v h264_vaapi -profile:v high -level 40 -r 24 -g 48 -bf 0 -b:v 2M -t 600 -c:a aac -b:a 32k -ar 16000 -ac 1 -shortest -movflags +faststart /home/roms/data/blink/live_stream_1/temp_videos/unavailable_v2.mp4
```

Change the following for the duration in sec:
`-t 240`