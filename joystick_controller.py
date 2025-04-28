from Gamepad import Gamepad
import socket
import time
import sys
import os.path
import yaml

# Make sure to run scripts/install.sh to install dependencies and build message
sys.path.append(os.path.abspath("selk_rc_msgs/build/python"))

import rc_channels_pb2

# TODO: clean-up file and styling

with open('config-yaml/mapping.yaml', 'r') as file:
    config = yaml.safe_load(file)

GAMEPAD_TYPE = config['GAMEPAD_TYPE']
MAPPINGS = config['MAPPINGS']

DEADBAND = 0.07 # TODO: Deadband per axis as some axis don't have deadband (triggers)
MIN_VALUE = 1000
NEUT_VALUE = 1500
MAX_VALUE = 2000

# UDP
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def axis_to_pwm(value):
    return NEUT_VALUE if abs(value) <= DEADBAND else int((value+1)*500 + 1000)

def button_to_pwm(value):
    return MAX_VALUE if value else MIN_VALUE

def print_msg(msg, channels):
    for channel in channels:
        print(f"\t{channel}:\t{getattr(msg,channel,None)}")
    print("---")


if __name__ == "__main__":
    axis = {0:0, 1:0, 4:0, 5:0}
    msg = rc_channels_pb2.RCChannels()

    channels = [attribute for attribute in dir(msg) if attribute.startswith("rc")]
    channels.sort()

    for channel in channels:
        setattr(msg, channel, 1500)

    # print_msg(msg, channels)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(MAPPINGS)
    print(GAMEPAD_TYPE)

    while not Gamepad.available():
        print("Waiting for gamepad...")
        time.sleep(3)

    gamepad = GAMEPAD_TYPE()

    try:
        while True:
            eventType, control, value = gamepad.getNextEvent()
            if control in MAPPINGS[eventType]:
                if MAPPINGS[eventType][control] in channels:
                    pwm_value = axis_to_pwm(value) if eventType == "AXIS" else button_to_pwm(value)

                    setattr(msg, MAPPINGS[eventType][control], pwm_value)
                else:
                    print(f"Channel {MAPPINGS[eventType][control]} doesn't exist" )
            else:
                print(f"Input {control} of type {eventType} is not mapped.")

            # print_msg(msg, channels)
            sock.sendto(msg.SerializeToString(), (UDP_IP, UDP_PORT))

    except BaseException as e:
        for channel in channels:
            setattr(msg, channel, NEUT_VALUE)

        sock.sendto(msg.SerializeToString(), (UDP_IP, UDP_PORT))
