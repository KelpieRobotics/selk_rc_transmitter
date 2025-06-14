from mappers import Mapper

from abc import ABC, abstractmethod

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

class ImageStitchMapping(TypedDict):
    mapping: Mapper
    min: int | float
    max: int | float
    step: int | float

class ImageStitchMappings(TypedDict):
    pan: ImageStitchMapping
    tilt: ImageStitchMapping | None

class SpecialFunction(ABC):
    @abstractmethod
    def run(self):
        "Run the special function"
        pass

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

    def __init__(self, mappings: ImageStitchMappings, port, output_dir, fps):

        self.mappings = mappings
        self.port = port
        self.output_dir = output_dir
        self.fps = fps

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
                        "!", "videorate", f"max-rate={self.fps}",
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

import math
import tkinter as tk
import numpy as np
import cv2
from PIL import Image, ImageTk, ImageDraw
import unittest

class StereoDistanceSpecialFunction(SpecialFunction):
    def __init__(self, offset: tuple[float, float, float], fov_deg: float, port1: int, port2: int, capture: bool = True, image_dir: str = None):
        self.T = np.array([[offset[0]], [offset[1]], [offset[2]]], dtype=np.float64)
        self.fov = math.radians(fov_deg)
        self.port1 = port1
        self.port2 = port2
        self.K = None
        self.P1 = None
        self.P2 = None

        self.image_dir = image_dir or os.path.join("images", "dist")
        os.makedirs(self.image_dir, exist_ok=True)
        self.imgL_path = os.path.join(self.image_dir, "img_1.jpg")
        self.imgR_path = os.path.join(self.image_dir, "img_2.jpg")

        if capture:
            self._capture_stereo_images()

    def _compute_intrinsics(self, width: int, height: int):
        fx = fy = (width / 2) / math.tan(self.fov / 2)
        cx = width / 2
        cy = height / 2
        self.K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float64)
        self.P1 = self.K @ np.hstack((np.eye(3), np.zeros((3,1))))
        self.P2 = self.K @ np.hstack((np.eye(3), self.T))

    def _capture_gst(self, port, filename):
        cmd = [
            "gst-launch-1.0", "-e",
            "udpsrc", f"port={port}", "caps=application/x-rtp,media=video,clock-rate=90000,encoding-name=H264,payload=96",
            "!", "rtph264depay",
            "!", "h264parse",
            "!", "avdec_h264",
            "!", "videoconvert",
            "!", "jpegenc",
            "!", f"filesink", f"location={filename}"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        proc.terminate()
        proc.wait()

    def _capture_stereo_images(self):
        self._capture_gst(self.port1, self.imgL_path)
        self._capture_gst(self.port2, self.imgR_path)

    def run(self):
        app = self._StereoApp(self)
        app.mainloop()

    def triangulate_from_points(self, pt1: tuple[int, int], pt2: tuple[int, int], image_shape: tuple[int, int]):
        height, width = image_shape
        self._compute_intrinsics(width, height)
        pts1 = np.array([[pt1[0]], [pt1[1]]], dtype=np.float64)
        pts2 = np.array([[pt2[0]], [pt2[1]]], dtype=np.float64)
        Xh = cv2.triangulatePoints(self.P1, self.P2, pts1, pts2)
        X = (Xh[:3] / Xh[3]).flatten()
        dist = np.linalg.norm(X)
        return X, dist

    class _StereoApp(tk.Tk):
        def __init__(self, parent):
            super().__init__()
            self.title("Stereo Distance Measurement")
            self.parent = parent
            self.left_panel = tk.Label(self, bd=2, relief="sunken")
            self.right_panel = tk.Label(self, bd=2, relief="sunken")
            self.left_panel.grid(row=0, column=0)
            self.right_panel.grid(row=0, column=1)
            self.left_panel.bind("<Button-1>", lambda e: self.on_click(e, 0))
            self.right_panel.bind("<Button-1>", lambda e: self.on_click(e, 1))

            self.pts = [None, None]
            self.pt_history = [[], []]  # Store all click points per image

            # Load original images
            self.orig_imgL = Image.open(self.parent.imgL_path)
            self.orig_imgR = Image.open(self.parent.imgR_path)

            # Resize to fit screen
            screen_w = self.winfo_screenwidth() // 2
            screen_h = self.winfo_screenheight() // 2
            self.orig_imgL.thumbnail((screen_w, screen_h), resample=Image.LANCZOS)
            self.orig_imgR.thumbnail((screen_w, screen_h), resample=Image.LANCZOS)

            self.imgL = self.orig_imgL.copy()
            self.imgR = self.orig_imgR.copy()

            w, h = self.imgL.size
            self.parent._compute_intrinsics(w, h)

            self.tkL = ImageTk.PhotoImage(self.imgL)
            self.tkR = ImageTk.PhotoImage(self.imgR)
            self.left_panel.config(image=self.tkL)
            self.right_panel.config(image=self.tkR)

            self.click_history = {0: [], 1: []}

        def on_click(self, event, side):
            pt = (event.x, event.y)
            self.click_history[side].append(pt)
            self.pts[side] = pt

            # Redraw image with persistent Xs and lines
            image = self.imgL.copy() if side == 0 else self.imgR.copy()
            draw = ImageDraw.Draw(image)

            # Draw all previous Xs
            for x, y in self.click_history[side]:
                draw.line((x-5, y-5, x+5, y+5), fill="red", width=2)
                draw.line((x-5, y+5, x+5, y-5), fill="red", width=2)

            # Draw line between last two points if 2+ clicks
            if len(self.click_history[side]) >= 2:
                draw.line((self.click_history[side][-2], self.click_history[side][-1]), fill="red", width=2)

            tk_image = ImageTk.PhotoImage(image)
            if side == 0:
                self.tkL = tk_image
                self.left_panel.config(image=self.tkL)
            else:
                self.tkR = tk_image
                self.right_panel.config(image=self.tkR)

            print(f"Clicked {'Left' if side==0 else 'Right'}: {pt}")
            if all(self.pts):
                self.triangulate()

        def draw_annotations(self):
            # Always draw on fresh copies
            self.imgL = self.orig_imgL.copy()
            self.imgR = self.orig_imgR.copy()
            drawL = ImageDraw.Draw(self.imgL)
            drawR = ImageDraw.Draw(self.imgR)

            # Draw all red Xs from history
            for pt in self.pt_history[0]:
                self._draw_red_x(drawL, pt)
            for pt in self.pt_history[1]:
                self._draw_red_x(drawR, pt)

            # Draw lines between matched points (same index in history)
            for i in range(min(len(self.pt_history[0]), len(self.pt_history[1]))):
                self._draw_red_line(drawL, self.pt_history[0][i], self.pt_history[1][i])
                self._draw_red_line(drawR, self.pt_history[0][i], self.pt_history[1][i])

            # Refresh display
            self.tkL = ImageTk.PhotoImage(self.imgL)
            self.tkR = ImageTk.PhotoImage(self.imgR)
            self.left_panel.config(image=self.tkL)
            self.right_panel.config(image=self.tkR)

        def _draw_red_x(self, draw, pt, size=5):
            x, y = pt
            draw.line((x - size, y - size, x + size, y + size), fill=(255, 0, 0), width=2)
            draw.line((x - size, y + size, x + size, y - size), fill=(255, 0, 0), width=2)

        def _draw_red_line(self, draw, pt1, pt2):
            draw.line((pt1[0], pt1[1], pt2[0], pt2[1]), fill=(255, 0, 0), width=1)

        def triangulate(self):
            (u1, v1), (u2, v2) = self.pts
            pts1 = np.array([[u1], [v1]], dtype=np.float64)
            pts2 = np.array([[u2], [v2]], dtype=np.float64)
            Xh = cv2.triangulatePoints(self.parent.P1, self.parent.P2, pts1, pts2)
            X = (Xh[:3] / Xh[3]).flatten()
            dist = np.linalg.norm(X)
            print(f"3D point: {X}, Distance from camera 1: {dist:.3f} meters")
            self.pts = [None, None]  # Clear current match only

class TestStereoDistance(unittest.TestCase):
    def test_stereo_gui_with_test_images(self):
        # Use test images without triggering GStreamer capture
        func = StereoDistanceSpecialFunction(
            offset=(0.1, 0.0, 0.0),
            fov_deg=65.6440,
            port1=5702,
            port2=5703,
            capture=False,  # Do NOT capture, just use test images
            image_dir="tests/images/dist"
        )

        # Check that images exist before running GUI
        self.assertTrue(os.path.exists(func.imgL_path), "img_1.jpg not found in test images")
        self.assertTrue(os.path.exists(func.imgR_path), "img_2.jpg not found in test images")

        # Launch the GUI (manual click required)
        print("Launching stereo GUI — click a matching point in both images to test triangulation.")
        func.run()

if __name__ == "__main__":
    unittest.main()



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
