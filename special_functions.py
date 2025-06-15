from custom_types import SpecialFunction, ImageStitchMappings


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

    def __init__(self, mappings: ImageStitchMappings, port: int | str, output_dir: str | None = os.path.join(os.path.dirname(__file__), "image_stitch"), **kwargs):
        self.mappings = mappings
        self.port = port

        # Default path
        if output_dir == "" or output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(__file__), "image_stitch", "")
        # Absolute path
        elif os.path.isabs(output_dir):
            self.output_dir = os.path.join(os.path.expandvars(output_dir), "")
        # Home dir path
        elif output_dir.startswith("~"):
            self.output_dir = os.path.expanduser(
                os.path.expandvars(
                    os.path.join(
                        os.path.dirname(__file__),
                        output_dir,
                        ""
                    )
                )
            )
        # Relative path
        else:
            self.output_dir = os.path.expandvars(
                os.path.join(
                    os.path.dirname(__file__), # Use the selk_rc_transmitter dir instead of pwd for consistency
                    output_dir,
                    ""
                )
            )

        self.state = ImageStitchSpecialFunction.State.IDLE

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
            if "tilt" in self.mappings and self.mappings["tilt"] is not None: self.mappings["tilt"]["mapping"].map(tilt_input, "set")

            for pan_input in range(self.mappings["pan"]["min"], self.mappings["pan"]["max"]+1, self.mappings["pan"]["step"]):
                self.mappings["pan"]["mapping"].map(pan_input, "set")

                print(f"Capturing image {images_taken}")
                proc = subprocess.Popen(
                    [
                        "gst-launch-1.0", "-e",
                        "udpsrc", f"port={self.port}", "caps=application/x-rtp,media=video,clock-rate=90000,encoding-name=H264,payload=96",
                        "!", "rtph264depay",
                        "!", "h264parse",
                        "!", "avdec_h264",
                        "!", "jpegenc", "snapshot=true",
                        "!", "filesink", f"location={os.path.join(images_dir, str(images_taken).zfill(3))}.jpg"
                    ],
                    preexec_fn=os.setsid  # UNIX/WSL: new process group for signaling
                )

                gst_rc = proc.wait()

                if gst_rc != 0:
                    print(f"Gstreamer exited with code {gst_rc}. Stopping capture...")

                    self.mappings["pan"]["mapping"].map(100, "reset")
                    if "tilt" in self.mappings and self.mappings["tilt"] is not None: self.mappings["tilt"]["mapping"].map(100, "reset")

                    self.state = ImageStitchSpecialFunction.State.IDLE
                    return False

                sleep(1)
                images_taken += 1

        jpg_files = [f for f in os.listdir(images_dir) if f.lower().endswith(".jpg")]

        # Sort based on filename stem (without extension)
        sorted_images = sorted([os.path.join(images_dir, f) for f in jpg_files])

        # Run the command and return
        proc = subprocess.Popen(
            [
                os.path.join(os.path.abspath(os.path.dirname(__file__)), "xpano", "build", "Xpano"),
                *sorted_images,
                "--gui"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        self.state = ImageStitchSpecialFunction
        print("Capture complete")
