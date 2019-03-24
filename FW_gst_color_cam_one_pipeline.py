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


import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
import FW_H264_PL
import argparse
import threading
import datetime
import time


class ColorCamOneProfile(FW_H264_PL.H264Pipeline):

    def __init__(self, video_device_path="/dev/video0"):
        FW_H264_PL.H264Pipeline.__init__(self, video_device_path)
        self.pipeline = None
        self.videosrc = None

        # Video elements related with writing to storage device
        self.filequeue = None
        self.fileparse = None
        self.filecap = None
        self.filesink = None

        # Video elements related with sending over network
        self.networkqueue = None
        self.decodebin = None
        self.videoconverter = None
        self.videoscale = None
        self.videorate = None
        self.videocap = None
        self.h264encoder = None
        self.videoparse = None
        self.rtpencoder = None
        self.udpsink = None

        # Tee related elements
        self.tee = None
        # For manual linkage :
        # self.tee_src_pad_template = None
        # self.tee_network_video_pad = None
        # self.network_videoqueue_pad = None
        # self.tee_file_video_pad = None
        # self.file_videoqueue_pad = None

    def gst_pipeline_color_cam_init(self, vid_src="/dev/video0", ip_addr="10.120.117.50"):

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
        self.is_linked = True

    def gst_pipeline_color_cam_init_with_file_store_static_fr_init(self, vid_src="/dev/video0", ip_addr="10.120.117.50",
                                                                   storage_location="/media/"):

        print("Initializing GST Pipeline")
        Gst.init(None)

        self.pipeline = Gst.parse_launch("v4l2src device=" + video_src + " ! video/x-h264,width=640,height=360 " +
                                         "! tee name=t ! queue ! filesink location=" + storage_location + "_%s" % \
                                         (datetime.datetime.now().strftime("%y%m%d%H%M")) + " t. ! queue ! rtph264pay "
                                         "! udpsink host=" + ip_addr + " port=5600")


    def gst_pipeline_color_cam_with_file_store_init(self, vid_src="/dev/video0", ip_addr="10.120.117.50",
                                                    storage_location="/media/"):

        print("Initializing GST Pipeline")
        Gst.init(None)

        # self.pipeline = Gst.Pipeline.new("h.264 to h.264")

        # Initialize video feed source
        print("Initializing v4l2 source")
        self.videosrc = Gst.ElementFactory.make("v4l2src", "vid-src")
        self.videosrc.set_property("device", vid_src)

        # Initialize the tee to split link into a file sink and a udp sink
        print("Initializing tee")
        self.tee = Gst.ElementFactory.make("tee", "tee")

        # Initialize file sink queue to be saved locally
        print("Initializing file sink queue")
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
                                   storage_location + "%s" % (datetime.datetime.now().strftime("%y%m%d%H%M")))

        # Initialize udp sink queue to be sent over udp/rtp
        print("Initializing network queue")
        self.networkqueue = Gst.ElementFactory.make("queue", "network-queue")

        # Initialize the binary decoder
        print("Initializing binary decoder")
        self.decodebin = Gst.ElementFactory.make("decodebin", "decode-bin")

        # Initialize the video converter
        print("Initializing video converter")
        self.videoconverter = Gst.ElementFactory.make("videoconvert", "vid-conv")

        # Initialize the videoscale converter
        print("Initializing video scaler")
        self.videoscale = Gst.ElementFactory.make("videoscale", "vid-scale")

        # Initialize the videorate converter
        print("Initializing video rate converter")
        self.videorate = Gst.ElementFactory.make("videorate", "vid-rate")

        # set up the Gst cap(s) for video/x-264 format
        print("Generating video cap")
        self.videocap = Gst.caps_from_string("video/x-raw,framerate=15/1,width=640,height=360")
        #self.videocap = Gst.caps_from_string("video/x-raw,width=640,height=360")

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
        #self.pipeline.add(self.videosrc)
        #self.pipeline.add(self.tee)
        # local file storage
        #self.pipeline.add(self.filequeue)
        #self.pipeline.add(self.fileparse)
        #self.pipeline.add(self.filesink)
        # to be sent off to network
        #self.pipeline.add(self.networkqueue)
        #self.pipeline.add(self.decodebin)
        #self.pipeline.add(self.videoconverter)
        #self.pipeline.add(self.videoscale)
        #self.pipeline.add(self.videorate)
        #self.pipeline.add(self.h264encoder)
        #self.pipeline.add(self.videoparse)
        #self.pipeline.add(self.rtpencoder)
        #self.pipeline.add(self.udpsink)

        print("Linking pipeline elements")

        # Link elements before tee
        #ret = self.videosrc.link(self.tee)

        # Link elements for file storage
        #ret = ret and self.filequeue.link_filtered(self.fileparse, self.filecap)
        #ret = ret and self.fileparse.link(self.filesink)

        # Link elements for network
        #ret = ret and self.networkqueue.link(self.decodebin)
        #ret = ret and self.decodebin.link(self.videoconverter)
        #ret = ret and self.videoconverter.link(self.videorate)
        #ret = ret and self.videorate.link(self.videoscale)
        #ret = ret and self.videoscale.link_filtered(self.h264encoder, self.videocap)
        #ret = ret and self.h264encoder.link(self.videoparse)
        #ret = ret and self.videoparse.link(self.rtpencoder)
        #ret = ret and self.rtpencoder.link(self.udpsink)

        #ret = ret and self.tee.link(self.networkqueue)
        #ret = ret and  self.tee.link(self.filequeue)

        # To manually link pads:
        # self.tee_src_pad_template = self.tee.get_pad_template("src_%u")
        # self.tee_network_video_pad = self.tee.request_pad(self.tee_src_pad_template, None, None)
        # self.network_videoqueue_pad = self.networkqueue.get_static_pad("sink")
        # self.tee_file_video_pad = self.tee.request_pad(self.tee_src_pad_template, None, None)
        # self.file_videoqueue_pad = self.filequeue.get_static_pad("sink")
        # self.tee_network_video_pad.link(self.network_videoqueue_pad)
        # self.tee_file_video_pad.link(self.file_videoqueue_pad)

        if not True:
            # print("Error: Elements could not be linked")
            self.is_linked = False
            # return
        else:
            self.is_linked = True

        # This is a place holder until decodebin -> video converter is figured out.
        self.pipeline = Gst.parse_launch("v4l2src device=/dev/video1 " +
                                             "! tee name=t ! queue ! video/x-h264, width=640, height=480 " +
                                             "! h264parse ! filesink location=" + storage_location +
                                             "%s" % (datetime.datetime.now().strftime("%y%m%d%H%M")) + " t. " +
                                             "! queue ! decodebin ! videoscale ! videorate " +
                                             "! video/x-raw,framerate=15/1,width=640,height=360 " +
                                             "! x264enc bitrate=500 speed-preset=superfast tune=zerolatency " +
                                             "! h264parse ! rtph264pay ! udpsink host=" + ip_addr + " port=5600 ")

        self.is_linked = True

    def color_cam_task(self, vid_src = "/dev/video1", ip_addr = "10.120.17.50"):
        print("Initializing video feed for " + vid_src + " :: " + ip_addr)
        self.gst_pipeline_color_cam_init(vid_src, ip_addr)
        self.start_feed()
        self.idle_task()

    def color_cam_with_file_store_static_fr_task(self, vid_src="/dev/video1", ip_addr="10.120.17.50",
                                                 media_path="/media/"):
        print("Initializing video feed for " + vid_src + " :: " + ip_addr)
        self.gst_pipeline_color_cam_init_with_file_store_static_fr_init(vid_src, ip_addr, media_path)
        self.start_feed()
        self.idle_task()

    def color_cam_with_file_store_task(self, vid_src="/dev/video1", ip_addr="10.120.17.50",
                                       media_path="/media/"):
        print("Initializing video feed for " + vid_src + " :: " + ip_addr)
        self.gst_pipeline_color_cam_with_file_store_init(vid_src, ip_addr, media_path)
        self.start_feed()
        self.idle_task()


def main(arg_in):

    # Initialize pipeline object
    pipeline = ColorCamOneProfile()
    # Initialized to True so that if Video device is not found, it only prints once.
    video_device_found = True
    # These are fillers.
    color_cam_1_present = True

    while True:

        # if a video device was found
        if len(FW_H264_PL.query_video_devices()) != 0:
            print("Video device(s) found:")
            print(FW_H264_PL.query_video_devices())
            video_device_found = True

            # this is a filler for color camera. Todo: Logic for checking which cam is present
            if color_cam_1_present:

                # Check that there is a storage device that flightwave has configured
                if len(FW_H264_PL.query_storage_devices()) != 0 and arg_in.wr == True:
                    video_feed_thread = threading.Thread(target=pipeline.color_cam_with_file_store_task,
                                                         args=["/dev/video1", arg_in.ip,
                                                               FW_H264_PL.query_storage_devices()[0]])
                    video_feed_thread.start()
                    time.sleep(1)

                # Store at same rate as stream
                elif arg_in.wrs == True:
                    print("Saving video to /home/main/aero_**")
                    video_feed_thread = threading.Thread(target=pipeline.color_cam_with_file_store_static_fr_task,
                                                         args=["/dev/video1", arg_in.ip, "/home/main/"])
                    video_feed_thread.start()
                    time.sleep(1)

                # Test saving locally
                elif arg_in.test == True:
                    print("Saving video to /home/main/test_video.h264")
                    video_feed_thread = threading.Thread(target=pipeline.color_cam_with_file_store_task,
                                                         args=["/dev/video1", arg_in.ip,
                                                               "/home/main/"])
                    video_feed_thread.start()
                    time.sleep(1)
                # No storage device so start pipeline with direct feed
                else:

                    video_feed_thread = threading.Thread(target=pipeline.color_cam_task,
                                                         args=["/dev/video1", arg_in.ip])
                    video_feed_thread.start()
                    time.sleep(1)

            while True:
                # Start user code here
                # check if video_feed_thread has joined. If yes, then exit from loop.
                if not pipeline.is_linked:
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
    arg_parser.add_argument("--wr", help="Write to storage device", action='store_true')
    arg_parser.add_argument("--wrs", help="Write to storage device at same rate as stream",action="store_true")
    arg_parser.add_argument("--test", help="Write to storage device test", action='store_true')
    args = arg_parser.parse_args()
    if args.ip:
        print("IP ADDR: " + args.ip)
        print("Saving Video?")
        print(args.wr)
        main(args)
    else:
        print("Missing target IP address to stream to.")