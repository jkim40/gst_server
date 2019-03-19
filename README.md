FLIGHTWAVE AEROSPACE SYSTEMS GST SERVER

Dependencies: 

    system: 
        libgirepository1.0-dev
        gcc
        libcairo2-dev
        pkg-config
        python-dev gir1.2-gtk-3.0
        python-gi
        python3-gi
        gstreamer1.0-tools
        gir1.2-gstreamer-1.0
        gir1.2-gst-plugins-base-1.0
        gstreamer1.0-plugins-good
        gstreamer1.0-plugins-ugly
        gstreamer1.0-plugins-bad
        gstreamer1.0-libav
    
    pip:
        pycairo
        PyGObject

    Commands: 
        sudo apt-get install python-pip3    
        sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python-dev gir1.2-gtk-3.0     
        sudo apt-get install python-gi python3-gi \
        gstreamer1.0-tools \
        gir1.2-gstreamer-1.0 \
        gir1.2-gst-plugins-base-1.0 \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-libav
        
        pip3 install pycairo
        pip3 install PyGObject    

System Configurations: 
    
    Startup Script rc.local: 
        
        python3 /home/gst_server/gst_feed_to_qgc.py
        
        
Test Gst Pipelines:

    Greyscale: 
        gst-launch-1.0 v4l2src device=/dev/video2 \
        ! videoparse format=nv12 width=640 height=512 \
        ! decodebin ! videoconvert ! x264enc ! queue \
        ! rtph264pay ! udpsink host=192.168.0.104 port=5600
        
    1080p Color: 
        gst-launch-1.0 v4l2src device=/dev/video1 \
        ! video/x-h264,width=1920,height=1080 \
        ! h264parse ! rtph264pay ! udpsink host=ip port=5600
        
    1080p Color with save to local storage:
        gst-launch-1.0 v4l2src device=/dev/video1 \ 
        ! tee name=t ! queue ! video/x-h264, width=640, height=480 \
        ! h264parse ! filesink location=/home/main/<insert name> t. \ 
        ! queue ! decodebin ! videoscale ! videorate \
        ! video/x-raw,framerate=15/1,width=640,height=360 \
        ! x264enc bitrate=500 speed-preset=superfast tune=zerolatency \
        ! h264parse ! rtph264pay ! udpsink host=ip port=5600 
        