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
import time
import gi
gi.require_version('Gst','1.0')
from gi.repository import Gst, GObject


class FlightwaveSupportedDevices:
    """Lists supported video devices

    This class is a static container for all Flightwave supported video devices.
    """

    color_1 = 0
    color_2 = 1
    thermal_1 = 2


class H264Pipeline:
    """Parent class for building Flightwave compatible gst pipeline profiles

    This class serves as a way to systematically build up camera codec pipelines for new cameras without cluttering
    a single script. It leaves the initialization of the pipelines up to the profile, and provides a unified way to
    start the pipeline.

    Attributes:
        pipeline: A gst pipeline to be initialized in a profile where this base class is inherited.
        is_linked: A boolean utilized to signal that the pipeline has been initialized, and the feed can start.
        video_device: Full path to video device associated with pipeline.
    """
    def __init__(self, video_device_path="/dev/video0"):
        self.pipeline = None
        self.is_linked = False
        self.video_device = video_device_path;

    def start_feed(self):
        if self.pipeline is not None and self.is_linked is True:
            print("Starting video feed...")
            self.pipeline.set_state(Gst.State.PAUSED)
            self.pipeline.set_state(Gst.State.PLAYING)
        else:
            print("Pipeline non-existent, or elements not yet linked")

    def stop_feed(self):
        print("Stopping video feed")
        self.pipeline.set_state(Gst.State.PAUSED)

    def idle_task(self):
        """Idle task provided for running while the feed is in operation.

            Runs a super loop that checks whether or not the associated video device is present. Closes thread when
            device is no longer present. Provided, but not required to run.

            Args:
                N/A

            Returns:
                N/A

            Raises:
                N/A
        """
        print("Entering idle task while video feeds.")
        while True:
            if len(query_video_devices()) == 0:
                print("Stopping feed...")
                self.stop_feed()
                self.is_linked = False
                print("Returning to main task...")
                break
            else:
                time.sleep(0.5)


def query_video_devices():
    # query /dev/ for video sources. Returns list of video devices
    device_path = "/dev"
    return [f for f in os.listdir(device_path) if "video" in f]


def query_storage_devices(device_path="/media"):
    """Query /media/ for storage devices.

        Retrieves a list of all storage devices pre-formatted by Flightwave Aero. If none are present,
        returns an empty list.

        Args:
            device_path: the directory to query for storage devices

        Returns:
            List of full path to video devices that are formatted to have 'aero' in name

        Raises:
            N/A

    """
    # query /media/ for storage devices. Returns list of video devices that are formatted to have aero in name

    return [f for f in os.listdir(device_path) if "aero" in f]


def main():
    """ Prints a description for this library

        Args:
            N/A

        Returns:
            N/A

        Raises:
            N/A
    """
    print("FW_H264_PL.py is a library containing the H264Pipeline class which serves as a generic interface for " +
          "device profiles to connect to Flightwave technology.")


if __name__ == "__main__":
    main()
