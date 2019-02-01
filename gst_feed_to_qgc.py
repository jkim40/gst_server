import threading
import time
import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst, GObject


class H264Pipeline:

    def __init__(self):
        self.pipeline = None
        self.videosrc = None
        self.videocap = None
        self.videoparse = None
        self.rtpencoder = None
        self.videosink = None
        self.islinked = False

    def gst_pipeline_h264_h264_init(self):

        print("Initializing GST Pipeline")
        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("h.264 to h.264")

        # Initialize video feed source
        print("Initializing v4l2 source")
        self.videosrc = Gst.ElementFactory.make("v4l2src","vid-src")
        self.videosrc.set_property("device", "/dev/video1")

        # set up the Gst cap(s) for video/x-264 format
        print("Generating video cap")
        self.videocap = Gst.caps_from_string("video/x-h264,width=1920,height=1080,framerate=30/1")

        # Initialize the video feed parser to parse h.264 frames
        print("Initializing video parser")
        self.videoparse = Gst.ElementFactory.make("h264parse","vid-parse")

        # Initialize rtp encoder
        print("Initializing rtp encoder")
        self.rtpencoder = Gst.ElementFactory.make("rtph264pay", "rtp-enc")

        # Initialize udp sink : requires ip address of qgc
        print("Initializing udp sink")
        self.udpsink = Gst.ElementFactory.make("udpsink","udp-sink")
        self.udpsink.set_property("host","192.168.0.101")
        self.udpsink.set_property("port",5600)

        # Add all elements to the pipeline
        "Adding all elements to pipeline"
        self.pipeline.add(self.videosrc)
        self.pipeline.add(self.videoparse)
        self.pipeline.add(self.rtpencoder)
        self.pipeline.add(self.udpsink)

        # Link elements together in order, with filter
        print("Linking pipeline elements")
        self.videosrc.link_filtered(self.videoparse,self.videocap)
        self.videoparse.link(self.rtpencoder)
        self.rtpencoder.link(self.udpsink)

        self.islinked = True

    def start_feed(self):
        if self.pipeline is not None\
        and self.islinked == True:
            print("Starting video feed")
            self.pipeline.set_state(Gst.State.PAUSED)
            self.pipeline.set_state(Gst.State.PLAYING)
        else:
            print("Pipeline non-existent, or elements not yet linked")

    def stop_feed(self):
        print("Stopping video feed")
        self.pipeline.set_state(Gst.State.PAUSED)

    def h264_to_h264_task(self):
        self.gst_pipeline_h264_h264_init()
        self.start_feed()


if __name__ == "__main__":

    pipeline = H264Pipeline()
    video_feed_thread = threading.Thread(target=pipeline.h264_to_h264_task)
    video_feed_thread.start()
    time.sleep(1)

    try:
        video_feed_thread.join()
        while True:
            time.sleep(1)

    except:
        print("Feed failed. Exiting")
        exit(0)
