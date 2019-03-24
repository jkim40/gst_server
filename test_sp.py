import subprocess
import os


command = "gst-launch-1.0 v4l2src device=/dev/video1 ! tee name=t ! queue ! video/x-h264,width=1920,height=1080 ! h264parse ! filesink location=/home/main/test t. !" + \
          " queue ! decodebin ! videoscale ! videorate ! video/x-raw,framerate=15/1,width=640,height=360 ! x264enc bitrate=500 speed-preset=superfast tune=zerolatency ! h264parse ! rtph264pay ! udpsink host=10.120.117.134 port=5600"
print(command)

p = subprocess.Popen([command], shell=True)

while p.poll() == None:
    # subprocess is still active. Do nothing.
    pass
