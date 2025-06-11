import sys
import os.path
from abc import ABC, abstractmethod
from typing import TypedDict, List
import socket

# Make sure to run scripts/install.sh to install dependencies and build message
sys.path.append(os.path.abspath("selk_rc_msgs/build/python"))

import rc_channels_pb2


outputters = [
    "selk_udp"
]

class NetworkTarget(TypedDict):
    host: str
    port: int

class Outputter(ABC):
    @abstractmethod
    def output(self, value, label = None):
        "Transmits a mapped value. Use `label` to specify which channel to use."

        pass

    @property
    @abstractmethod # TODO: remove abstract, make default return empty list and allow Outputters that don't have special labels to just rely on base class implementation?
    def labels(self)-> List[str]:
        "Returns the list of special labels that can be used."

        pass

# TODO: Add NetworkOutputter in between or would it be too abstracted?

class UdpOutputter(Outputter):
    def __init__(self, target: NetworkTarget):
        self.target = target

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data):
        return self.sock.sendto(data, (self.target["host"], self.target["port"])) == len(data)

class SelkUdpOutputter(UdpOutputter):
    def __init__(self, target):
        super().__init__(target)

        self.msg = rc_channels_pb2.RCChannels()

    def __print_msg(self):
        for channel in self.labels:
            print(f"\t{channel}:\t{getattr(self.msg, channel, None)}")
        print("---")

    def output(self, value, label: str | None = None):
        if label is None or label == "":
            print("Output label is required to specify the channel")

            return False

        if label not in self.labels:
            print(label, "is not a valid channel")

        setattr(self.msg, label, int(value*10))

        self.__print_msg()

        return self.send(self.msg.SerializeToString())

    @property
    def labels(self):
        return [attribute for attribute in dir(self.msg) if attribute.startswith("rc")]

