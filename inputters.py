# TODO: limit outputs to -100, 100 for all mappers
# TODO: Mapper interface
# TODO: Expo

from mappers import Mapper

from abc import ABC, abstractmethod
import time


axis_inputters = [
    "normal",
    "absolute_weight",
    "scaled_weight"
]

button_inputters = [
    "normal",
    "impulse"
]


class Inputter(ABC):
    def __init__(self, mapping: Mapper, mapping_label = None):
        self.mapping = mapping
        self.mapping_label = mapping_label

    @abstractmethod
    def process(self, value):
        pass

class AxisInputter(Inputter):
    def __init__(self, mapping: Mapper, mapping_label = None, weight = 100, min = -100, max = 100, center = 0, deadband = 0, neutral = 0):
        super().__init__(mapping, mapping_label)
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
        return self.mapping.map(self.transform(value), self.mapping_label)


class NormalAxisInputter(AxisInputter):
    def __init__(self, mapping: Mapper, mapping_label = None, weight=100, min=-100, max=100, center=0, deadband=0, neutral = 0, **kwargs):
        super().__init__(mapping, mapping_label, weight, min, max, center, deadband, neutral)

    def transform(self, value):
        value *= 100

        if abs(value) <= self.deadband:
            return self.center
        elif value > 0:
            if self.max >= 0:
                output = (self.weight)/(100-self.deadband)*(value-self.deadband)+self.center

                if output >= 100 and self.max >= 100:
                    return 100
                elif output >= self.max:
                    return self.max
                else:
                    return output
            else:
                output = (-self.weight)/(100-self.deadband)*(value-self.deadband)+self.center

                if output <= -100 and self.max <= -100:
                    return -100
                elif output <= self.max:
                    return self.max
                else:
                    return output
        else:
            if self.min <= 0:
                output = (self.weight)/(100-self.deadband)*(value+self.deadband)+self.center

                if output <= -100 and self.min <= -100:
                    return -100
                elif output <= self.min:
                    return self.min
                else:
                    return output
            else:
                output = (-self.weight)/(100-self.deadband)*(value+self.deadband)+self.center

                if output >= 100 and self.min >= 100:
                    return 100
                elif output >= self.min:
                    return self.min
                else:
                    return output


class AbsoluteWeightAxisInputter(AxisInputter):
    def __init__(self, mapping: Mapper, mapping_label = None, weight=100, min=-100, max=100, center=0, deadband=0, neutral = 0, **kwargs):
        super().__init__(mapping, mapping_label, weight, min, max, center, deadband, neutral)

    def transform(self, value):
        value *= 100

        if abs(value) <= self.deadband:
            return self.center
        elif value > 0:
            if self.max >= 0:
                output = (self.weight-self.center)/(100-self.deadband)*(value-self.deadband)+self.center

                if output >= 100 and self.max >= 100:
                    return 100
                elif output >= self.max:
                    return self.max
                else:
                    return output
            else:
                output = (-self.weight-self.center)/(100-self.deadband)*(value-self.deadband)+self.center

                if output <= -100 and self.max <= -100:
                    return -100
                elif output <= self.max:
                    return max
                else:
                    return output
        else:
            if self.min <= 0:
                output = (self.center+self.weight)/(100-self.deadband)*(value+self.deadband)+self.center

                if output <= -100 and self.min <= -100:
                    return -100
                elif output <= self.min:
                    return self.min
                else:
                    return output
            else:
                output = (self.center-self.weight)/(100-self.deadband)*(value+self.deadband)+self.center

                if output >= 100 and self.min >= 100:
                    return 100
                elif output >= self.min:
                    return self.min
                else:
                    return output

class ScaledWeightAxisInputter(AxisInputter):
    def __init__(self, mapping: Mapper, mapping_label = None, min=-100, max=100, center=0, deadband=0, neutral = 0, **kwargs):
        super().__init__(mapping, mapping_label, 100, min, max, center, deadband, neutral)

    def transform(self, value):
        value *= 100

        if abs(value) <= self.deadband:
            return self.center
        elif value > 0:
            output = (self.max-self.center)/(100-self.deadband)*(value-self.deadband)+self.center

            if max >= 0 and output >= 100:
                return 100
            elif max < 0 and output <= -100:
                return -100
            else:
                return output
        else:
            output = (self.center-self.min)/(100-self.deadband)*(value+self.deadband)+self.center

            if min <= 0 and output <= -100:
                return -100
            elif min > 0 or output >= 100:
                return 100
            else:
                return output


class ButtonInputter(Inputter):
    def __init__(self, mapping: Mapper, mapping_label = None, released=-100, pressed=100):
        super().__init__(mapping, mapping_label)

        self.released = released
        self.pressed = pressed


class NormalButtonInputter(ButtonInputter):
    def __init__(self, mapping: Mapper, mapping_label = None, released=-100, pressed=100):
        super().__init__(mapping, mapping_label, released, pressed)

    def process(self, value):
        return self.mapping.map(self.pressed if value else self.released, self.mapping_label)


class ImpulseButtonInputter(ButtonInputter):
    def __init__(self, mapping: Mapper, mapping_label = None, released=-100, pressed=100, delay=0.1):
        super().__init__(mapping, mapping_label, released, pressed, self.mapping_label)

        self.delay = delay

    def process(self, value):
        if value:
            if not self.mapping.map(self.pressed, self.mapping_label):
                return False

            time.sleep(self.delay)

            return self.mapping.map(self.released, self.mapping_label)
