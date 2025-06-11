from sshkeyboard import listen_keyboard
from typing import Optional, List, Tuple
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from enum import Enum, auto
from time import sleep, time
from pathlib import Path

import sys
import os
import shutil
import signal
import subprocess

KEY_BINDING = "c"

class State(Enum):
    IDLE = auto()
    CAPTURE = auto()

    def next(self) -> 'State':
        match self:
            case State.IDLE:
                return State.CAPTURE
            case State.CAPTURE:
                return State.IDLE
            case _:
                raise NotImplementedError()


def capture_images(output_dir: str = "./images/tmp", port: int = 5702, fps: float | str=2):
    # ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    gst_cmd = [
        "gst-launch-1.0", "-e",
        "udpsrc", f"port={port}",
        "caps=application/x-rtp,media=video,clock-rate=90000,encoding-name=H264,payload=96", "!",
        "rtph264depay", "!",
        "h264parse", "!",
        "avdec_h264", "!",
        "videoconvert", "!",
        "videorate", f"max-rate={fps}", "!",
        "jpegenc", "!",
        f"multifilesink", f"location={output_dir}/%05d.jpg"
    ]

    print("Starting GStreamer capture pipeline...")
    proc = subprocess.Popen(
        gst_cmd,
        preexec_fn=os.setsid  # UNIX/WSL: new process group for signaling
    )

    def cleanup(signum, frame):
        print(f"Signal {signum} received: terminating gst-launch...")
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)  # Graceful terminate
        proc.wait()
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    # proc.wait()
    # print("GStreamer pipeline stopped.")
    try:
        while True:
            ret = proc.poll()
            if ret is not None:
                print("GStreamer pipeline exited")
                break
            sleep(0.1)  # check periodically
    except KeyboardInterrupt:
        pass
    finally:
        print("Terminating GStreamer pipeline...")
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)  # Graceful terminate
        proc.wait()


def stitch_images(sub_dir: str = "tmp"):
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # image_dir = Path(f"./images/{sub_dir}")
    # jpg_files = [f for f in image_dir.iterdir() if f.suffix.lower() == ".jpg"]
    # sorted_images = [str(path) for path in sorted(jpg_files, key=lambda f: int(f.stem))]

    # print(sorted_images)

    cmd = [f"{current_dir}/xpano/build/Xpano"] #, *sorted_images]
    
    # Run the command and wait
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print(line, end="")

    def cleanup(signum, frame):
        print(f"Signal {signum} received: terminating gst-launch...")
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)  # Graceful terminate
        proc.wait()
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    proc.wait()

def create_dir(path):
    if os.path.exists(path):
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    else:
        os.makedirs(path)

def sticher_process(rx: Connection):
    prev_state: Optional[State] = None
    state: State = State.IDLE

    capture_dir: Optional[str] = None
    capture_thread: Optional[Process] = None

    stitching_dirs: List[str] = []
    stitching_threads: List[Process] = []

    # intialize folders
    create_dir("./images/tmp")
    create_dir("./tmp")

    while True:
        _ = rx.recv()

    # def tmp(key):
    #     nonlocal state
    #     nonlocal worker_thread
    #     if key != KEY_BINDING:
    #         return

        # Clean up any existing threads
        size = len(stitching_threads)
        for i in range(size):
            i = size - i - 1
            if not stitching_threads[i].is_alive():
                stitching_threads[i].terminate()
                stitching_threads[i].join()

                del stitching_dirs[i]
                del stitching_threads[i]
        
        print(f"stitching threads: {stitching_threads}")

        print(f"current state - {state}\t previous state - {prev_state}")

        match (prev_state, state):
            # Resets state
            case (None | State.CAPTURE , State.IDLE): # next state is Capture
                capture_dir = f"{int(time())}"
                create_dir(f"./images/{capture_dir}")
                
                worker_thread = Process(
                    target = capture_images,
                    args=[f"./images/{capture_dir}", 5702, 1]
                )

                worker_thread.start()

                capture_thread = worker_thread
            
            # Start stitching images
            case (State.IDLE, State.CAPTURE):
                print("TIME TO STITCH")
                print("Killing capture thread...")                
                capture_thread.terminate()
                capture_thread.join()
                capture_thread = None
                
                worker_thread = Process(
                    target = stitch_images,
                    args=[capture_dir]
                )

                worker_thread.start()

                stitching_dirs.append(capture_dir)
                stitching_threads.append(worker_thread)
            case _:
                raise NotImplementedError()
        
        # update state
        print("updating state...")
        prev_state = state
        state = state.next()
        print(f"updated state - {state}\t previous state - {prev_state}")

if __name__ == "__main__":
    (tx, rx) = Pipe()

    _process = Process(
        target=sticher_process,
        args=[rx]
    )

    _process.start()

    def on_release(key):
        if key == KEY_BINDING:
            tx.send(1)

    listen_keyboard(
        on_release=on_release,
    )
