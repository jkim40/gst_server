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

import argparse
import subprocess
import time
import gi
import FW_H264_PL

gi.require_version('Gst', '1.0')


def main(arg_in):

    # Initialized to True so that if Video device is not found, it only prints once.
    video_device_found = True

    # Target video device. Profile should be defined for the device.
    target_video_device = FW_H264_PL.FlightwaveSupportedDevices.color_1

    # Full path for target video device
    video_device_full_path = ""

    while True:

        # if a video device was found
        if len(FW_H264_PL.query_video_devices()) != 0:

            video_device_found = True

            print("Video device(s) found:")
            print(FW_H264_PL.query_video_devices())

            # This is a filler. Todo: Logic for checking which cam is present. Return device full path.

            if target_video_device == FW_H264_PL.FlightwaveSupportedDevices.color_1:
                video_device_full_path = "/dev/video1"

                if FW_H264_PL.query_storage_devices():
                p = subprocess.Popen(["python3","/home/main/startup/gst_server/FW_gst_color_cam_one_pipeline.py","-ip",
                                      "10.120.117.134", "--wrs"])

            elif target_video_device == FW_H264_PL.FlightwaveSupportedDevices.color_2:

                # TODO: Start the subprocess for opening up a profile
                pass

            elif target_video_device == FW_H264_PL.FlightwaveSupportedDevices.thermal_1:

                # TODO: Start the subprocess for opening up a profile
                pass

            while True:
                # Start user code here
                # Todo: Check if subprocess is active, and associated video device exists. Exit otherwise.
                if video_device_full_path[5:len(video_device_full_path)] not in str(FW_H264_PL.query_video_devices()):
                    print(FW_H264_PL.query_video_devices())
                    print(video_device_full_path[5:len(video_device_full_path)])
                    print("Video feed has ended.")
                    p.kill()
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
