from Gamepad import Gamepad
import socket
import time
import sys
import os.path
import yaml

# Make sure to run scripts/install.sh to install dependencies and build message
sys.path.append(os.path.abspath("selk_rc_msgs/build/python"))

import rc_channels_pb2

with open('config-yaml/mapping.yaml', 'r') as file:
    config = yaml.safe_load(file)

GAMEPAD_TYPE = config['GAMEPAD_TYPE']
MAPPINGS = config['MAPPINGS']

channel_centers = {}

# UDP
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def get_centers():
    for input, config in MAPPINGS.get("AXIS", {}).items():
        channel = config.get("channel")
        center = config.get("center")
        if channel and center is not None:
            channel_centers[channel] = center

def axis_to_pwm(value, config):
    deadband = config.get('deadband', 0.07)
    center = config.get('center')
    min_val = config.get('min')
    max_val = config.get('max')

    if abs(value) <= deadband:
        return center

    # Scale value from -1 to 1
    if value > 0:
        return int(center + (max_val - center) * value)
    else:
        return int(center + (center - min_val) * value)

def button_to_pwm(value, config):
    return config['max'] if value else config['min']

def print_msg(msg, channels):
    for channel in channels:
        print(f"\t{channel}:\t{getattr(msg, channel, None)}")
    print("---")

if __name__ == "__main__":
    msg = rc_channels_pb2.RCChannels()
    channels = sorted([attribute for attribute in dir(msg) if attribute.startswith("rc")])

    get_centers()

    print(channel_centers)

    for channel in channels:
        setattr(msg, channel, channel_centers.get(channel, 1500))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("channels:", channels)
    print("Mapped AXIS inputs:", list(MAPPINGS["AXIS"].keys()))
    print("Mapped BUTTON inputs:", list(MAPPINGS["BUTTON"].keys()))

    while not Gamepad.available():
        print("Gamepad not detected. Retrying in 3 seconds...")
        time.sleep(3)

    gamepad = GAMEPAD_TYPE()
    print("Gamepad connected.")

    try:
        while True:
            eventType, control, value = gamepad.getNextEvent()

            print(f"Input Event - Type: {eventType}, Control: {control}, Value: {value}")

            # AXIS input handling
            if eventType == "AXIS" and control in MAPPINGS["AXIS"]:
                axis_config = MAPPINGS["AXIS"][control]
                channel = axis_config.get('channel')

                if channel in channels:
                    pwm_value = axis_to_pwm(value, axis_config)
                    setattr(msg, channel, pwm_value)
                    print(f"AXIS → Set {channel} = {pwm_value}")
                else:
                    print(f"[Warning] Axis channel '{channel}' not found in RCChannels message.")

            # BUTTON input handling
            elif eventType == "BUTTON" and control in MAPPINGS["BUTTON"]:
                button_config = MAPPINGS["BUTTON"][control]
                channel = button_config.get('channel')
                if channel in channels:
                    pwm_value = button_to_pwm(value, button_config)
                    setattr(msg, channel, pwm_value)
                    print(f"BUTTON → Set {channel} = {pwm_value}")
                else:
                    print(f"[Warning] Button channel '{channel}' not found in RCChannels message.")

            else:
                print(f"[Unmapped] Input '{control}' of type '{eventType}' is not mapped.")

            #print_msg(msg, channels)

            sock.sendto(msg.SerializeToString(), (UDP_IP, UDP_PORT))

    except BaseException as e:
        print(f"[Exception] {e}")
        for channel in channels:
            setattr(msg, channel, channel_centers.get(channel, 1500))
        sock.sendto(msg.SerializeToString(), (UDP_IP, UDP_PORT))

