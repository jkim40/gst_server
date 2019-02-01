import threading
import datetime
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
        self.networkqueue = None
        self.filequeue = None
        self.rtpencoder = None
        self.videosink = None
        self.filesink = None
        self.tee = None
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

        # Initialize the tee to split link into a file sink and a udp sink
        print("Initializing tee")
        self.tee = Gst.ElementFactory.make("Tee","Tee")

        # Initialize file sink queue to be saved locally
        print("Initializing fil sink queue")
        self.filequeue = Gst.ElementFactory.make("queue", "file-queue")

        # Initialize file sink
        print("Initializing local file sink")
        self.filesink = Gst.ElementFactory.make("filesink","file-sink")
        self.filesink.set_property("location","/home/aero_%s"%(datetime.datetime.now().strftime("%y%m%d%H%M")))

        # Initialize udp sink queue to be sent over udp/rtp
        print("Initializing network queue")
        self.networkqueue = Gst.ElementFactory.make("queue","network-queue")

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
        self.pipeline.add(self.tee)
        self.pipeline.add(self.filequeue)
        self.pipeline.add(self.filesink)
        self.pipeline.add(self.networkqueue)
        self.pipeline.add(self.rtpencoder)
        self.pipeline.add(self.udpsink)

        # Link elements together in order, with filter
        print("Linking pipeline elements")

        # Link elements before tee
        self.videosrc.link_filtered(self.videoparse,self.videocap)
        self.videoparse.link(self.tee)

        # Link elements after tee regarding network
        self.networkqueue.link(self.rtpencoder)
        self.rtpencoder.link(self.udpsink)

        # Link elements after tee regarding file sink
        self.filequeue.link(self.filesink)

        # Link tee to elements after tee
        self.tee.link(self.networkqueue)
        self.tee.link(self.filequeue)

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
