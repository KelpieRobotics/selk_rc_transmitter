from outputters import Outputter

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List


mappers = [
    "passthrough",
    "relative",
    "add",
    "toggle_latch"
]

class Mapper(ABC):
    def __init__(self, output: Outputter, output_label=None, min=-100, max=100, center=0, **kwargs):
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



class PassthroughMapper(Mapper):
    def map(self, input, label = None):
        return self.output.output(self._clip_output(input), self.output_label)

    @property
    def labels(self):
        return []


# FIXME: self.state only gets updated when its input gets changed! This makes it useless for axis inputs unless the same value would be sent periodically.
#        Make it so it gets update in dt with a given speed (steps/s) instead off on each input change.
class RelativeMapper(Mapper):
    def __init__(self, output: Outputter, output_label=None, min=-100, max=100, center=0, speed = 20, **kwargs):
        super().__init__(output, output_label, min, max, center)

        self.speed = speed

        self.state = self.center

    def get_state(self):
        return self.state

    def map(self, input, label = None):
        if label == "set":
            self.state = self._clip_output(input)

            return self.output.output(self.state, self.output_label)

        elif label == "reset":
            if input > 0:
                self.state = self._clip_output(self.center)

                return self.output.output(self.state, self.output_label)
            else:
                return True # Don't transmit on input going back to neutral

        delta = input / 100 * self.speed

        self.state = self._clip_output(self.state + delta)

        return self.output.output(self.state, self.output_label)

    @property
    def labels(self):
        return ["set", "reset"]


class AddMapper(Mapper):
    def __init__(self, output: Outputter, output_label=None, min=-100, max=100, center=0, **kwargs):
        super().__init__(output, output_label, min, max, center)

        self.left = 0
        self.right = 0

    def map(self, input, label = None):
        if label == "left":
            self.left = input
        elif label == "right":
            self.right = input
        else:
            # TODO: Log unknown label
            pass

        output = self.left + self.right

        return self.output.output(self._clip_output(output), self.output_label)

    @property
    def labels(self):
        return ["left", "right"]

# TODO: untested
class ToggleLatchMapper(Mapper):
    class States(Enum):
        UNLATCHED = auto()
        PRELATCHED = auto() # Used to prevent preliminary unlatching
        LATCHED = auto()
        PREUNLATCHED = auto() # Used to prevent preliminary latching

    def __init__(self, output: Outputter, output_label=None, min=-100, max=100, center=0, **kwargs):
        super().__init__(output, output_label, min, max, center)

        self.state = ToggleLatchMapper.States.UNLATCHED

    def map(self, input, label = None):
        match self.state:
            case ToggleLatchMapper.States.UNLATCHED:
                if input >= self.center:
                    self.state = ToggleLatchMapper.States.PRELATCHED
            case ToggleLatchMapper.States.PRELATCHED:
                if input < self.center:
                    self.state = ToggleLatchMapper.States.LATCHED
            case ToggleLatchMapper.States.LATCHED:
                if input >= self.center:
                    self.state = ToggleLatchMapper.States.PREUNLATCHED
            case ToggleLatchMapper.States.PREUNLATCHED:
                if input < self.center:
                    self.state = ToggleLatchMapper.States.UNLATCHED

        return self.output.output(self._clip_output(self.max if self.state == ToggleLatchMapper.States.LATCHED or self.state == ToggleLatchMapper.States.PRELATCHED else self.min), self.output_label)

    @property
    def labels(self):
        return []
