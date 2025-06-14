from custom_types import SpecialFunction, ImageStitchMappings


# TODO: clean dependencies of legacy code at the bottom of the file

from typing import TypedDict #, Optional, List, Dict
# from multiprocessing import Process, Pipe
# from multiprocessing.connection import Connection
from enum import Enum, auto
# from time import sleep, time
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

    def __init__(self, mappings: ImageStitchMappings, port, output_dir, **kwargs):

        self.mappings = mappings
        self.output_dir = output_dir
        self.port = port

        self.state = ImageStitchSpecialFunction.State.IDLE

        if not os.path.exists(os.path.join(self.output_dir, "images")):
            os.makedirs(os.path.join(self.output_dir, "images"))


    def run(self):
        # ensure output directory exists
        images_taken = 0
        self.state = ImageStitchSpecialFunction.State.CAPTURE

        for tilt_input in range(self.mappings["tilt"]["min"], self.mappings["tilt"]["max"]+1, self.mappings["tilt"]["step"]) if self.mappings["tilt"] is not None else range(1):
            if self.mappings["tilt"] is not None: self.mappings["tilt"]["mapping"].map(tilt_input, "set")

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
                        "!", "videoconvert",
                        "!", "videorate", "max-rate=30",
                        "!", "jpegenc",
                        "!", f"filesink", f"location={self.output_dir}/{images_taken}.jpg"
                    ],
                    preexec_fn=os.setsid  # UNIX/WSL: new process group for signaling
                )

                gst_rc = proc.wait()

                if gst_rc != 0:
                    print(f"Gstreamer exited with code {gst_rc}. Stopping capture...")

                    self.mappings["pan"]["mapping"].map(100, "reset")
                    if self.mappings["tilt"] is not None: self.mappings["tilt"]["mapping"].map(100, "reset")

                    self.state = ImageStitchSpecialFunction.State.IDLE
                    return False



        current_dir = os.path.dirname(__file__)

        image_dir = os.path.join(current_dir, "images", sub_dir)
        jpg_files = [
            f for f in os.listdir(image_dir)
            if f.lower().endswith(".jpg")
        ]

        # Sort based on filename stem (without extension)
        sorted_images = sorted(
            [os.path.join(image_dir, f) for f in jpg_files],
            key=lambda f: int(os.path.splitext(os.path.basename(f))[0])
        )

        # Run the command and return
        proc = subprocess.Popen(
            [
                os.path.join(current_dir, "xpano", "build", "Xpano"),
                *sorted_images,
                "--gui"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        self.state = ImageStitchSpecialFunction

# TODO: legacy code, check if needed
# def create_dir(path):
#     if os.path.exists(path):
#         for filename in os.listdir(path):
#             file_path = os.path.join(path, filename)
#             if os.path.isfile(file_path) or os.path.islink(file_path):
#                 os.unlink(file_path)
#             elif os.path.isdir(file_path):
#                 shutil.rmtree(file_path)
#     else:
#         os.makedirs(path)

# def sticher_process(rx: Connection):
#     prev_state: Optional[State] = None
#     state: State = State.IDLE

#     capture_dir: Optional[str] = None
#     capture_thread: Optional[Process] = None

#     stitching_dirs: List[str] = []
#     stitching_threads: List[Process] = []

#     # intialize folders
#     create_dir("./images/tmp")
#     create_dir("./tmp")

#     while True:
#         _ = rx.recv()

#     # def tmp(key):
#     #     nonlocal state
#     #     nonlocal worker_thread
#     #     if key != KEY_BINDING:
#     #         return

#         # Clean up any existing threads
#         size = len(stitching_threads)
#         for i in range(size):
#             i = size - i - 1
#             if not stitching_threads[i].is_alive():
#                 stitching_threads[i].terminate()
#                 stitching_threads[i].join()

#                 del stitching_dirs[i]
#                 del stitching_threads[i]

#         print(f"stitching threads: {stitching_threads}")

#         print(f"current state - {state}\t previous state - {prev_state}")

#         match (prev_state, state):
#             # Resets state
#             case (None | State.CAPTURE , State.IDLE): # next state is Capture
#                 capture_dir = f"{int(time())}"
#                 create_dir(f"./images/{capture_dir}")

#                 worker_thread = Process(
#                     target = capture_images,
#                     args=[f"./images/{capture_dir}", 5702, 1]
#                 )

#                 worker_thread.start()

#                 capture_thread = worker_thread

#             # Start stitching images
#             case (State.IDLE, State.CAPTURE):
#                 print("TIME TO STITCH")
#                 print("Killing capture thread...")
#                 capture_thread.terminate()
#                 capture_thread.join()
#                 capture_thread = None

#                 worker_thread = Process(
#                     target = stitch_images,
#                     args=[capture_dir]
#                 )

#                 worker_thread.start()

#                 stitching_dirs.append(capture_dir)
#                 stitching_threads.append(worker_thread)
#             case _:
#                 raise NotImplementedError()

#         # update state
#         print("updating state...")
#         prev_state = state
#         state = state.next()
#         print(f"updated state - {state}\t previous state - {prev_state}")
