import configs
import mappers

from Gamepad import Gamepad
import socket
import time
import sys
import os.path


# TODO: argparse
# TODO: multiple mappings to the same channel


# Make sure to run scripts/install.sh to install dependencies and build message
sys.path.append(os.path.abspath("selk_rc_msgs/build/python"))

import rc_channels_pb2



# TODO: instead of checking which sender is in use, and with what settings, perform the check in the load_config() and assign to a different common var
def send(msg, link):
    if link["protocol"].lower() == "udp":
        target = config["link"]["target"].split(":")

        sock.sendto(msg.SerializeToString(), (target[0], target[1] if len(target) > 1 else 5005)) # TODO: move default port elsewhere


def print_msg(msg, channels):
    for channel in channels:
        print(f"\t{channel}:\t{getattr(msg, channel, None)}")
    print("---")


if __name__ == "__main__":
    msg = rc_channels_pb2.RCChannels()
    available_channels = [attribute for attribute in dir(msg) if attribute.startswith("rc")]

    config = configs.load_config('config.yaml', available_channels) # TODO: Config command-line argument

    for input_config in config["mappings"]["axis"]:
        setattr(msg, input_config["channel"], input_config["center"])

    for input_config in config["mappings"]["button"]:
        setattr(msg, input_config["channel"], input_config["released"])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # print("Available channels:", available_channels)
    # print("Mapped AXIS inputs:", list(config["mappings"]["axis"].keys()))
    # print("Mapped BUTTON inputs:", list(config["mappings"]["button"].keys()))

    while not Gamepad.available():
        print("Gamepad not detected. Retrying in 3 seconds...")
        time.sleep(3)

    gamepad = getattr(config["gamepad"])()
    print("Gamepad connected.")

    try:
        while True:
            eventType, control, value = gamepad.getNextEvent()

            print(f"Input Event - Type: {eventType}, Control: {control}, Value: {value}")

            # AXIS input handling
            if eventType == "AXIS" and control in config["mappings"]["axis"]:
                axis_config = config["mappings"]["axis"][control]
                channel_value = mappers.map_to_channel_range(getattr(mappers, "axis_"+axis_config["mode"])(value, **axis_config))

                setattr(msg, axis_config['channel'], channel_value)
                # print(f"AXIS → Set {axis_config['channel']} = {channel_value}")

            # TODO: Bookmark

            # BUTTON input handling
            elif eventType == "BUTTON" and control in config["mappings"]["button"]:
                button_config = config["mappings"]["button"][control]
                channel_value = mappers.map_to_channel_range(getattr(mappers, "button_"+button_config["mode"])(value, **button_config))

                setattr(msg, button_config['channel'], channel_value)
                # print(f"BUTTON → Set {button_config['channel']} = {channel_value}")

            else:
                print(f"[Unmapped] Input '{control}' of type '{eventType}' is not mapped.")


            if "link" in config:
                send(msg, config["link"])
            else:
                print("No link entry in the config") # TODO: Move config validation to load_config()

    except BaseException as e:
        print(f"[Exception] {e}")
        for input_config in config["mappings"]["axis"]:
            setattr(msg, input_config["channel"], input_config["center"])

        for input_config in config["mappings"]["button"]:
            setattr(msg, input_config["channel"], input_config["released"])

        if "link" in config:
            send(msg, config["link"])
        else:
            print("No link entry in the config") # TODO: Move config validation to load_config()

