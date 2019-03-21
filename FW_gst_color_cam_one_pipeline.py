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

import os
import argparse
import threading
import datetime
import time
import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst, GObject
import FW_H264_PL


class ColorCamOneProfile(FW_H264_PL.H264Pipeline):

    def __init__(self, ):
        self.pipeline = None
        self.videosrc = None
        self.videocap = None
        self.filecap = None
        self.videoparse = None
        self.fileparse = None
        self.rawqueue = None
        self.decodebin = None
        self.videoconverter = None
        self.h264encoder = None
        self.networkqueue = None
        self.filequeue = None
        self.rtpencoder = None
        self.filesink = None
        self.udpsink = None
        self.tee = None
        self.islinked = False

    def gst_pipeline_color_cam_init(self, vid_src = "/dev/video0",ip_addr="10.120.117.50"):

        print("Initializing GST Pipeline")
        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("h.264 to h.264")

        # Initialize video feed source
        print("Initializing v4l2 source")
        self.videosrc = Gst.ElementFactory.make("v4l2src","vid-src")
        self.videosrc.set_property("device", vid_src)

        # set up the Gst cap(s) for video/x-264 format
        print("Generating video cap")
        # self.videocap = Gst.caps_from_string("video/x-h264,width=1920,height=1080")
        # self.videocap = Gst.caps_from_string("video/x-h264,width=1280,height=720")
        # self.videocap = Gst.caps_from_string("video/x-h264,width=640,height=480")
        self.videocap = Gst.caps_from_string("video/x-h264,width=640,height=360")

        # Initialize the video feed parser to parse h.264 frames
        print("Initializing video parser")
        self.videoparse = Gst.ElementFactory.make("h264parse", "vid-parse")

        # Initialize udp sink queue to be sent over udp/rtp
        print("Initializing network queue")
        self.networkqueue = Gst.ElementFactory.make("queue","network-queue")

        # Initialize rtp encoder
        print("Initializing rtp encoder")
        self.rtpencoder = Gst.ElementFactory.make("rtph264pay", "rtp-enc")

        # Initialize udp sink : requires ip address of qgc
        print("Initializing udp sink")
        self.udpsink = Gst.ElementFactory.make("udpsink","udp-sink")
        print("Setting port : %s, host 5600" % ip_addr)
        self.udpsink.set_property("host", ip_addr)
        self.udpsink.set_property("port", 5600)

        # Add all elements to the pipeline
        print("Adding all elements to pipeline")
        self.pipeline.add(self.videosrc)
        self.pipeline.add(self.videoparse)
        self.pipeline.add(self.networkqueue)
        self.pipeline.add(self.rtpencoder)
        self.pipeline.add(self.udpsink)

        # Link elements together in order, with filter
        print("Linking pipeline elements")

        self.videosrc.link_filtered(self.videoparse, self.videocap)
        self.videoparse.link(self.networkqueue)
        self.networkqueue.link(self.rtpencoder)
        self.rtpencoder.link(self.udpsink)
        self.islinked = True

    def gst_pipeline_color_cam_with_file_store_init(self, vid_src = "/dev/video0", ip_addr="10.120.117.50",
                                                    storage_location="/media/aero/"):

        print("Initializing GST Pipeline")
        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("h.264 to h.264")

        # Initialize video feed source
        print("Initializing v4l2 source")
        self.videosrc = Gst.ElementFactory.make("v4l2src", "vid-src")
        self.videosrc.set_property("device", vid_src)

        # Initialize the tee to split link into a file sink and a udp sink
        print("Initializing tee")
        self.tee = Gst.ElementFactory.make("tee", "tee")

        # Initialize file sink queue to be saved locally
        print("Initializing fil sink queue")
        self.filequeue = Gst.ElementFactory.make("queue", "file-queue")

        # Initialize the video feed parser to parse h.264 frames
        print("Initializing video parser")
        self.fileparse = Gst.ElementFactory.make("h264parse", "file-parse")

        # set up the Gst cap(s) for video/x-264 format
        print("Generating video cap")
        self.filecap = Gst.caps_from_string("video/x-h264,width=640,height=480")

        # Initialize file sink
        print("Initializing local file sink")
        self.filesink = Gst.ElementFactory.make("filesink", "file-sink")
        self.filesink.set_property("location",
                                   storage_location + "/%s" % (datetime.datetime.now().strftime("%y%m%d%H%M")))

        # Initialize udp sink queue to be sent over udp/rtp
        print("Initializing network queue")
        self.networkqueue = Gst.ElementFactory.make("queue", "network-queue")

        # Initialize the binary decoder
        print("Initializing binary decoder")
        self.decodebin = Gst.ElementFactory.make("decodebin","decode-bin")

        # todo: initialize videoscale and video rate here

        # set up the Gst cap(s) for video/x-264 format
        print("Generating video cap")
        self.videocap = Gst.caps_from_string("video/x-raw,framerate=15/1,width=640,height=360")

        # Initialize encoder todo: modify encoder for encoding with set parameters bitrate, speed-preset=superfast and
        # todo: tune=zerolatency, if possible
        print("Initializing h264 video encoder")
        self.h264encoder = Gst.ElementFactory.make("x264enc", "h264-enc")

        # Initialize the video feed parser to parse h.264 frames
        print("Initializing video parser")
        self.videoparse = Gst.ElementFactory.make("h264parse", "vid-parse")

        # Initialize rtp encoder
        print("Initializing rtp encoder")
        self.rtpencoder = Gst.ElementFactory.make("rtph264pay", "rtp-enc")

        # Initialize udp sink : requires ip address of qgc
        print("Initializing udp sink")
        self.udpsink = Gst.ElementFactory.make("udpsink", "udp-sink")
        self.udpsink.set_property("host", ip_addr)
        self.udpsink.set_property("port", 5600)

        # Add all elements to the pipeline
        print("Adding all elements to pipeline")
        self.pipeline.add(self.videosrc)
        self.pipeline.add(self.tee)
        self.pipeline.add(self.filequeue)
        self.pipeline.add(self.filecap)
        self.pipeline.add(self.fileparse)
        self.pipeline.add(self.filesink)
        self.pipeline.add(self.networkqueue)
        self.pipeline.add(self.decodebin)
        # this is a filler for videoscale
        # this is a filler for videorate
        self.pipeline.add(self.videocap)
        self.pipeline.add(self.h264encoder)
        self.pipeline.add(self.videoparse)
        self.pipeline.add(self.rtpencoder)
        self.pipeline.add(self.udpsink)

        # Link elements together in order, with filter. todo: finish linking these objects together
        print("Linking pipeline elements")

        # Link elements before tee
        self.videosrc.link_filtered(self.videoparse,self.videocap)
        self.videoparse.link(self.tee)
        # Link elements after tee regarding network
        self.networkqueue.link(self.rtpencoder)
        self.rtpencoder.link(self.udpsink)
        # Link elements after tee regarding file sink
        self.filequeue.link(self.filesink)

        self.tee.link(self.filequeue)
        self.tee.link(self.networkqueue)

        self.islinked = False

    def start_feed(self):
        if self.pipeline is not None and self.islinked is True:
            print("Starting video feed...")
            self.pipeline.set_state(Gst.State.PAUSED)
            self.pipeline.set_state(Gst.State.PLAYING)
        else:
            print("Pipeline non-existent, or elements not yet linked")

    def stop_feed(self):
        print("Stopping video feed")
        self.pipeline.set_state(Gst.State.PAUSED)

    def color_cam_task(self, vid_src = "/dev/video1", ip_addr = "10.120.17.50"):
        print("Initializing video feed for " + vid_src + " :: " + ip_addr)
        self.gst_pipeline_color_cam_init(vid_src, ip_addr)
        self.start_feed()
        self.idle_task()

    def color_cam_with_file_store_task(self, vid_src = "/dev/video1", ip_addr= "10.120.17.50",
                                       media_path = "/media/aero/"):
        print("Initializing video feed for " + vid_src + " :: " + ip_addr)
        self.gst_pipeline_color_cam_with_file_store_init(vid_src, ip_addr,media_path)
        self.start_feed()
        self.idle_task()

    def idle_task(self):
        print("Entering idle task while video feeds.")
        while True:
            if len(query_video_devices()) == 0:
                print("Stopping feed")
                self.stop_feed()
                self.islinked = False
                print("Returning to main task...")
                break
            else:
                time.sleep(0.5)


def query_video_devices():
    # query /dev/ for video sources. Returns list of video devices
    device_path = "/dev"
    return [f for f in os.listdir(device_path) if "video" in f]


def query_storage_devices():
    # query /media/ for storage devices. Returns list of video devices that are formatted to have aero in name
    device_path = "/media"
    return [f for f in os.listdir(device_path) if "aero" in f]


def main(arg_in):

    # Initialize pipeline object
    pipeline = H264Pipeline()
    # Initialized to True so that if Video device is not found, it only prints once.
    video_device_found = True
    # These are fillers.
    color_cam_1_present = True
    thermal_cam_present = False

    while True:

        # if a video device was found
        if len(query_video_devices()) != 0:
            print("Video device(s) found:")
            print(query_video_devices())
            video_device_found = True

            # this is a filler for color camera. Todo: Logic for checking which cam is present
            if color_cam_1_present:

                # Check that there is a storage device that flightwave has configured
                if len(query_storage_devices()) != 0:
                    video_feed_thread = threading.Thread(target=pipeline.color_cam_with_file_store_task,
                                                         args=["/dev/video1", arg_in.ip, query_storage_devices()[0]])
                    video_feed_thread.start()
                    time.sleep(1)

                # No storage device so start pipeline with direct feed
                else:

                    video_feed_thread = threading.Thread(target=pipeline.color_cam_task,
                                                         args=["/dev/video1", arg_in.ip])
                    video_feed_thread.start()
                    time.sleep(1)

            elif thermal_cam_present:
                pass

            while True:
                # Start user code here
                # check if video_feed_thread has joined. If yes, then exit from loop.
                if not pipeline.islinked:
                    print("Video feed has ended.")
                    break

        else:
            if video_device_found:
                print("No video device found. Please plug in a Flightwave supported video device...")
                video_device_found = False
            time.sleep(1)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-ip", help="IP address of ground control", type=str)
    args = arg_parser.parse_args()
    if args.ip:
        print("IP ADDR: " + args.ip)
        main(args)
    else:
        print("Missing target IP address to stream to.")

