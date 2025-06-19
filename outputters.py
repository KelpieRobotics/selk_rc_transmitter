import sys
import os.path

# Make sure to run scripts/install.sh to install dependencies and build message
sys.path.append(os.path.abspath("selk_rc_msgs/build/python"))

import rc_channels_pb2

from custom_types import UdpOutputter, NetworkTarget

outputters = [
    "selk_udp"
]

class SelkUdpOutputter(UdpOutputter):
    def __init__(self, target: NetworkTarget, **kwargs):
        super().__init__(target)

        self.msg = rc_channels_pb2.RCChannels()

    def __print_msg(self):
        for channel in self.labels:
            print(f"\t{channel}:\t{getattr(self.msg, channel, None)}")
        print("---")

    def __map_ardupilot_pwm(value):
        """
        Ardusub allows adds a 10% margin on each side of the input range in case of signal loss.

        This function maps the value to the 10%-90% range which is 1000-2000us range in ardupilot.
        """
        return 8 * value

    def __map_full_range(value):
        return 10 * value

    def output(self, value, label: str | None = None):
        if label is None or label == "":
            print("Output label is required to specify the channel")

            return False

        if label not in self.labels:
            print(label, "is not a valid channel")

        # setattr(self.msg, label, int(SelkUdpOutputter.__map_ardupilot_pwm(value)))
        setattr(self.msg, label, int(SelkUdpOutputter.__map_full_range(value)))

        # self.__print_msg()
        # print(self.msg.SerializeToString().hex())

        return self.send(self.msg.SerializeToString())

    @property
    def labels(self):
        return [attribute for attribute in dir(self.msg) if attribute.startswith("rc")]

