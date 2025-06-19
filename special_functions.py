from custom_types import SpecialFunction, ImageStitchSpecialFunctionMappings, ImageStitchSpecialFunctionMapping
from utils import resolve_path

# TODO: clean dependencies of legacy code at the bottom of the file

from typing import TypedDict #, Optional, List, Dict
# from multiprocessing import Process, Pipe
# from multiprocessing.connection import Connection
from enum import Enum, auto
from time import sleep
# from pathlib import Path

# import sys
import os
# import shutil
# import signal
import subprocess


special_functions = [
    "image_stitch"
]

class ImageStitchSpecialFunction(SpecialFunction):
    class State(Enum):
        IDLE = auto()
        CAPTURE = auto()

        def next(self):
            match self:
                case ImageStitchSpecialFunction.State.IDLE:
                    return ImageStitchSpecialFunction.State.CAPTURE
                case ImageStitchSpecialFunction.State.CAPTURE:
                    return ImageStitchSpecialFunction.State.IDLE
                case _:
                    raise NotImplementedError()

    def __init__(self, mappings: ImageStitchSpecialFunctionMappings, port: int | str, ptgui_exec_file: str = "~/.local/share/ptgui/PTGui", output_dir: str | None = os.path.join(os.path.dirname(__file__), "panorama"), **kwargs):
        self.mappings = mappings
        self.port = port
        self.ptgui_exec_file = resolve_path(ptgui_exec_file, "~/.local/share/ptgui/PTGui")
        self.output_dir = resolve_path(output_dir, os.path.join(os.path.dirname(__file__), "panorama"))

        self.state = ImageStitchSpecialFunction.State.IDLE

    def __map(mapping: ImageStitchSpecialFunctionMapping, value):
        if mapping["mode"] == "absolute":
            mapping["mapping"].map(value, "set")

        elif mapping["mode"] == "relative":
            mapping["mapping"].map(value)
            sleep(1)
            mapping["mapping"].map(mapping["center"])

        else:
            raise ValueError(mapping["mode"], "is not valid ImageStitchSpecialFunctionMapping[\"mode\"] value")

    def __reset(mapping: ImageStitchSpecialFunctionMapping):
        if mapping["mode"] == "absolute":
            mapping["mapping"].map(100, "reset")

        elif mapping["mode"] == "relative":
            pass

        else:
            raise ValueError(mapping["mode"], "is not valid ImageStitchSpecialFunctionMapping[\"mode\"] value")

    def run(self):
        images_dir = os.path.join(self.output_dir, "images")

        # ensure output directory exists
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        # if it exists, ensure it's empty
        elif len(os.listdir(images_dir)) != 0:
            for item in os.listdir(images_dir):
                os.remove(os.path.join(images_dir,item)) # Will throw an error if directory contains non-empty directories

        images_taken = 0
        self.state = ImageStitchSpecialFunction.State.CAPTURE

        for tilt_input in range(self.mappings["tilt"]["min"], self.mappings["tilt"]["max"]+1, self.mappings["tilt"]["step"]) if "tilt" in self.mappings and self.mappings["tilt"] is not None else range(1):
            if "tilt" in self.mappings and self.mappings["tilt"] is not None: ImageStitchSpecialFunction.__map(self.mappings["tilt"], tilt_input)

            for pan_input in range(self.mappings["pan"]["min"], self.mappings["pan"]["max"]+1, self.mappings["pan"]["step"]):
                ImageStitchSpecialFunction.__map(self.mappings["pan"], pan_input)

                sleep(2) # Let the stream stabilize before capturing

                print(f"Capturing image {images_taken}")
                proc = subprocess.Popen(
                    [
                        "gst-launch-1.0", "-e",
                        "udpsrc", f"port={self.port}", "caps=\"application/x-rtp,media=video,clock-rate=90000,encoding-name=(string)H264,payload=(int)96,width=(int)1920,height=(int)1080\"",
                        "!", "rtph264depay", "request-keyframe=true", "wait-for-keyframe=true",
                        "!", "h264parse",
                        "!", "avdec_h264", "output-corrupt=false",
                        "!", "jpegenc",  "snapshot=true", "quality=97",
                        "!", "filesink", f"location={os.path.join(images_dir, str(images_taken).zfill(3))}.jpg"
                    ],
                    # preexec_fn=os.setsid  # UNIX/WSL: new process group for signaling
                )

                gst_rc = proc.wait()

                if gst_rc != 0:
                    print(f"Gstreamer exited with code {gst_rc}. Stopping capture...")

                    ImageStitchSpecialFunction.__reset(self.mappings["pan"])
                    if "tilt" in self.mappings and self.mappings["tilt"] is not None: ImageStitchSpecialFunction.__reset(self.mappings["tilt"])

                    self.state = ImageStitchSpecialFunction.State.IDLE
                    return False

                images_taken += 1

        jpg_files = [f for f in os.listdir(images_dir) if f.lower().endswith(".jpg")]

        # Sort based on filename stem (without extension)
        sorted_images = sorted([os.path.join(images_dir, f) for f in jpg_files])

        # Run the command and return
        proc = subprocess.Popen(
            [
                self.ptgui_exec_file,
                "-createproject",
                *sorted_images,
                "-output", os.path.join(self.output_dir, "panorama.pts"),
                # "-template", os.path.join(os.path.dirname(__file__), "template.pts"),
                "-stitchnogui", os.path.join(self.output_dir, "panorama.pts")
            ],
            # stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        proc.wait()

        proc = subprocess.Popen(
            [
                "xdg-open",
                os.path.join(self.output_dir, "panorama.jpg")
            ],
            # stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        ImageStitchSpecialFunction.__reset(self.mappings["pan"])
        if "tilt" in self.mappings and self.mappings["tilt"] is not None: ImageStitchSpecialFunction.__reset(self.mappings["tilt"])
        self.state = ImageStitchSpecialFunction
        print("Capture complete")
