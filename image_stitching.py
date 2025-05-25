from sshkeyboard import listen_keyboard
from typing import Optional
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from enum import Enum, auto
from time import sleep

import sys
import os
import shutil
import signal
import subprocess

KEY_BINDING = "c"

class State(Enum):
    IDLE = auto()
    CAPTURE = auto()
    STITCH = auto()

    def next(self) -> 'State':
        match self:
            case State.IDLE:
                return State.CAPTURE
            case State.CAPTURE:
                return State.STITCH
            case State.STITCH:
                return State.IDLE
            case _:
                raise NotImplementedError()


def capture_images(output_dir: str = "./images", port: int = 5701, fps: float | str=2):
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
        f"multifilesink", f"location={output_dir}/frame_%05d.jpg"
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


def stitch_images():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = [f"{current_dir}/xpano/build/Xpano"]
    
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
    state: State = State.IDLE
    worker_thread: Optional[Process] = None

    # intialize folders
    create_dir("./images")
    create_dir("./tmp")

    while True:
        _ = rx.recv()

    # def tmp(key):
    #     nonlocal state
    #     nonlocal worker_thread
    #     if key != KEY_BINDING:
    #         return
        
        if worker_thread is not None:
            worker_thread.terminate()
            worker_thread.join()
            worker_thread = None
        
        state = state.next()

        print(f"Currently - {state}")

        match state:
            # Resets state
            case State.IDLE:
                create_dir("./images")
                # create_dir("./tmp")
            
            # capture images using gstreamer
            case State.CAPTURE: 
                worker_thread = Process(
                    target = capture_images,
                    args=["./images", 5701, 1]
                )

                worker_thread.start()       
                
            case State.STITCH:
                worker_thread = Process(
                    target = stitch_images
                )

                worker_thread.start()
            case _:
                raise NotImplementedError()

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
