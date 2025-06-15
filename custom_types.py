from typing import TypedDict, List, Dict, Any
from typing_extensions import Required
from abc import ABC, abstractmethod

import socket

# Data types
class NetworkTarget(TypedDict):
    host: str
    port: int

# Base classes
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

class SpecialFunction(ABC):
    @abstractmethod
    def run(self):
        "Run the special function"
        pass

class Mapper(ABC):
    def __init__(self, output: Outputter, output_label=None, min=-100, max=100, center=0):
        self.output = output
        self.output_label = output_label

        self.min = min
        self.max = max
        self.center = center

    def _clip_output(self, value):
        if value >= 100 and self.max >= 100:
            return 100
        elif value >= self.max:
            return self.max
        elif value <= -100 and self.min <= -100:
            return -100
        elif value <= self.min:
            return self.min
        else:
            return value

    @abstractmethod
    def map(self, input, label = None):
        pass

    @property
    @abstractmethod # TODO: remove abstract, make default return empty list and allow Mappers that don't have special labels to just rely on base class implementation?
    def labels(self) -> List[str]:
        "Returns the list of special labels that can be used."

        pass

class Inputter(ABC):
    def __init__(self, mapping_or_function: Mapper | SpecialFunction, mapping_label = None):
        self.mapping = mapping_or_function
        self.mapping_label = mapping_label

    @abstractmethod
    def process(self, value):
        pass

    @abstractmethod
    def map(self, value, label):
        pass

class AxisInputter(Inputter):
    def __init__(self, mapping_or_function: Mapper | SpecialFunction, mapping_label = None, weight = 100, min = -100, max = 100, center = 0, deadband = 0, neutral = 0):
        super().__init__(mapping_or_function, mapping_label)
        self.weight = weight
        self.min = min
        self.max = max
        self.center = center
        self.deadband = deadband
        self.neutral = neutral

    @abstractmethod
    def transform(self, value):
        "Calculate the output based on a given input"
        pass

    def process(self, value):
        return self.map(self.transform(value), self.mapping_label)

    def map(self, value, label):
        if isinstance(self.mapping, Mapper):
            self.mapping.map(value, label)
        elif isinstance(self.mapping, SpecialFunction):
            if value > self.center: self.mapping.run()
        else: raise ValueError("self.mapping is not a Mapper nor SpecialFunction.")

class ButtonInputter(Inputter):
    def __init__(self, mapping_or_function: Mapper | SpecialFunction, mapping_label = None, released=-100, pressed=100):
        super().__init__(mapping_or_function, mapping_label)

        self.released = released
        self.pressed = pressed

    def map(self, value, label):
        if isinstance(self.mapping, Mapper):
            self.mapping.map(value, label)
        elif isinstance(self.mapping, SpecialFunction):
            if value == self.pressed: self.mapping.run()
        else: raise ValueError("self.mapping is not a Mapper nor SpecialFunction.")

# Config types
## Input configs
class InputConfig(TypedDict, total=False):
    mapping: Required[str | int | None]
    mode: str

class AxisInputConfig(InputConfig, total=False):
    weight: int | float
    min: int | float
    max: int | float
    center: int | float
    deadband: int | float
    neutral: int | float

class ButtonInputConfig(InputConfig, total=False):
    released: int | float
    pressed: int | float

class InputsConfig(TypedDict, total=False):
    axes: Dict[str | int, AxisInputConfig | str | int]
    buttons: Dict[str | int, ButtonInputConfig | str | int]

class Inputs(TypedDict):
    axes: Dict[str | int, AxisInputter]
    buttons: Dict[str | int, ButtonInputter]

## Mapping configs
class MappingConfig(TypedDict, total=False):
    output: Required[str | int | None]
    type: str
    min: int | float
    max: int | float
    center: int | float
    speed: int | float


## Special Function configs
class SpecialFunctionMapping(TypedDict):
    mapping: str | int | None | Mapper

class SpecialFunctionConfig(TypedDict):
    function: Required[str]
    mappings: Dict[str | int, SpecialFunctionMapping | str | int]

### Image Stitch configs
class ImageStitchSpecialFunctionMapping(SpecialFunctionMapping, total = False):
    min: int | float
    max: int | float
    step: int | float

class ImageStitchMappings(TypedDict, total = False):
    pan: Required[ImageStitchSpecialFunctionMapping | str | int]
    tilt: ImageStitchSpecialFunctionMapping | str | int | None

class ImageStitchSpecialFunctionConfig(SpecialFunctionConfig):
    mappings: ImageStitchMappings
    output_dir: str
    port: int

## Output configs
class OutputConfig(TypedDict):
    type: str
    target: Dict[str, Any]


## Config
class Config(TypedDict):
    gamepad: str
    inputs: InputsConfig
    mappings: Dict[str | int, MappingConfig | str | int]
    special_functions: Dict[str | int, SpecialFunctionConfig]
    outputs: Dict[str | int, OutputConfig]


