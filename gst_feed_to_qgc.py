#!/usr/bin/evn python
"""
GST server.

This piece of software is property of Flightwave Aerospace Systems. Its primary
use is to stream images to a ground controller running qground control over UDP.
It does so by utilizing GST v1.0. For questions and concerns, see Flightwave
Aerospace Systems.

Parameters:
    None

Returns:
    None

"""
__author__ = "Hong Kim"
__copyright__ = "Copyright 2019, Flightwave Aerospace Systems"

import threading
import datetime
import time
import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst, GObject
import subprocess
import os
import argparse


class H264Pipeline:

    def __init__(self):
        self.pipeline = None
        self.videosrc = None
        self.videocap = None
        self.videoparse = None
        self.rawqueue = None
        self.decodebin = None
        self.videoconverter = None
        self.h264encoder = None
        self.networkqueue = None
        self.filequeue = None
        self.rtpencoder = None
        self.videosink = None
        self.filesink = None
        self.tee = None
        self.islinked = False

    def gst_pipeline_raw_h264_init(self, vid_src = "/dev/video0",ip_addr="10.120.17.50"):
        print("Initializing GST Pipeline")
        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("raw to h.264")

        # Initialize video feed sourcefrom
        print("Initializing v4l2 source")
        self.videosrc = Gst.ElementFactory.make("v4l2src","vid-src")
        self.videosrc.set_property("device", vid_src)

        # set up the Gst cap(s) for video/x-264 format
        print("Generating video cap")
        self.videocap = Gst.caps_from_string("video/x-raw,format=nv12,width=640,height=512")

        # Initialize the video feed parser to parse raw frames
        print("Initializing video parser")
        self.videoparse = Gst.ElementFactory.make("rawvideoparse","vid-parse")

        # Initialize the binary decoder
        print("Initializing binary decoder")
        self.decodebin = Gst.ElementFactory.make("decodebin","decode-bin")

        # Initialize the video converter
        print("Initializing video converter")
        self.videoconverter = Gst.ElementFactory.make("videoconvert","vid-conv")

        # Initialize encoder
        print("Initializing h264 video encoder")
        self.h264encoder = Gst.ElementFactory.make("x264enc","h264-enc")

        # Initialize the tee to split link into a file sink and a udp sink
        print("Initializing tee")
        self.tee = Gst.ElementFactory.make("tee","tee")

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
        self.udpsink.set_property("host",ip_addr)
        self.udpsink.set_property("port",5600)

        # Add all elements to the pipeline
        print("Adding all elements to pipeline")
        self.pipeline.add(self.videosrc)
        self.pipeline.add(self.videoparse)
        self.pipeline.add(self.decodebin)
        self.pipeline.add(self.videoconverter)
        self.pipeline.add(self.h264encoder)
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
        self.videoparse.link(self.decodebin)
        self.decodebin.link(self.videoconverter)
        self.videoconverter.link(self.h264encoder)
        self.h264encoder.link(self.tee)

        # Link elements after tee regarding network
        self.networkqueue.link(self.rtpencoder)
        self.rtpencoder.link(self.udpsink)

        # Link elements after tee regarding file sink
        self.filequeue.link(self.filesink)

        # Link tee to elements after tee
        # self.tee.link(self.networkqueue)
        self.tee.link(self.filequeue)
        self.tee.link(self.networkqueue)

        self.islinked = True

    def gst_pipeline_h264_h264_init(self,vid_src = "/dev/video0",ip_addr = "10.120.117.50"):

        print("Initializing GST Pipeline")
        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("h.264 to h.264")

        # Initialize video feed source
        print("Initializing v4l2 source")
        self.videosrc = Gst.ElementFactory.make("v4l2src","vid-src")
        self.videosrc.set_property("device", "/dev/video1")

        # set up the Gst cap(s) for video/x-264 format
        print("Generating video cap")
        # self.videocap = Gst.caps_from_string("video/x-h264,width=1920,height=1080,framerate=30/1")
        # self.videocap = Gst.caps_from_string("video/x-h264,width=1280,height=720,framerate=30/1")
        # self.videocap = Gst.caps_from_string("video/x-h264,width=640,height=480,framerate=30/1")
        self.videocap = Gst.caps_from_string("video/x-h264,width=640,height=360,framerate=30/1")

        # Initialize the video feed parser to parse h.264 frames
        print("Initializing video parser")
        self.videoparse = Gst.ElementFactory.make("h264parse","vid-parse")

        # Initialize the tee to split link into a file sink and a udp sink
        print("Initializing tee")
        self.tee = Gst.ElementFactory.make("tee","tee")

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
        self.udpsink.set_property("host",ip_addr)
        self.udpsink.set_property("port",5600)

        # Add all elements to the pipeline
        print("Adding all elements to pipeline")
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

        if True:
            # Link elements before tee
            self.videosrc.link_filtered(self.videoparse,self.videocap)
            self.videoparse.link(self.tee)
        else:
            self.videosrc.link_filtered(self.videoparse,self.videocap) 
            self.videoparse.link(self.networkqueue)

        # Link elements after tee regarding network
        self.networkqueue.link(self.rtpencoder)
        self.rtpencoder.link(self.udpsink)

        # Link elements after tee regarding file sink
        self.filequeue.link(self.filesink)

        if True:
            # Link tee to elements after tee
            self.tee.link(self.filequeue)
            self.tee.link(self.networkqueue)

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

    def h264_to_h264_task(self, vid_src = "/dev/video0", ip_addr = "10.120.17.50"):
        # for d in query_video_devices():
        #     print(d)


        # Check compression formats for the video sources
        # Prioritize the following : h264 nv12 mjpeg yuyv.
        # The reason for this prioritization is to put h264 with the best compression specs first, followed by what is
        # known to be used only in the thermal cams that flightwave provides. It is, however, uncompressed. mjpeg be-
        # cause it is compressed, though transcoding needs to occur. And then yuyv or yuv, which is raw. It is possibly
        # better to take raw videos and directly compress instead of transcoding a compressed mjpeg.
        print("Initializing video feed for " + vid_src + " :: " + ip_addr)
        self.gst_pipeline_h264_h264_init(vid_src, ip_addr)
        # self.gst_pipeline_raw_h264_init("/dev/video2")
        self.start_feed()

def query_video_devices():
    # query /dev/ for video sources. Returns list of video devices 
    device_path = "/dev" 
    return [f for f in os.listdir(device_path) if "video" in f]

def get_video_formats(vid_src = "/dev/video0"):
    # current place holder
    pass


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-ip", help="IP address of ground control",
                            type=str)
    arg_parser.add_argument("-dev", help="Video device full path",
                            type=str)
    args = arg_parser.parse_args()
    print("IP ADDR: " + args.ip)
    print("DEVICE: " + args.dev)

    pipeline = H264Pipeline()
    # pipeline.gst_pipeline_h264_h264_init(args.dev,args.IP)
    video_feed_thread = threading.Thread(target=pipeline.h264_to_h264_task, args=[args.dev,args.ip])
    video_feed_thread.start()
    time.sleep(1)

    try:
        video_feed_thread.join()
        while True:
            # Start user code here
            # check if video_feed_thread has joined. If yes, then exit from loop.
            time.sleep(1)

    except:
        print("Feed failed. Exiting")
        exit(0)
