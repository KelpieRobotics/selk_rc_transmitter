# TODO: limit outputs to -100, 100 for all mappers
# TODO: Mapper interface
# TODO: Expo

from custom_types import AxisInputter, ButtonInputter, Mapper, SpecialFunction

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

class NormalAxisInputter(AxisInputter):
    def __init__(self, mapping_or_function: Mapper | SpecialFunction, mapping_label = None, weight=100, min=-100, max=100, center=0, deadband=0, neutral = 0, **kwargs):
        super().__init__(mapping_or_function, mapping_label, weight, min, max, center, deadband, neutral)

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
    def __init__(self, mapping_or_function: Mapper | SpecialFunction, mapping_label = None, weight=100, min=-100, max=100, center=0, deadband=0, neutral = 0, **kwargs):
        super().__init__(mapping_or_function, mapping_label, weight, min, max, center, deadband, neutral)

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
    def __init__(self, mapping_or_function: Mapper | SpecialFunction, mapping_label = None, min=-100, max=100, center=0, deadband=0, neutral = 0, **kwargs):
        super().__init__(mapping_or_function, mapping_label, 100, min, max, center, deadband, neutral)

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


class NormalButtonInputter(ButtonInputter):
    def __init__(self, mapping_or_function: Mapper | SpecialFunction, mapping_label = None, released=-100, pressed=100, **kwargs):
        super().__init__(mapping_or_function, mapping_label, released, pressed)

    def process(self, value):
        return self.map(self.pressed if value else self.released, self.mapping_label)


class ImpulseButtonInputter(ButtonInputter):
    def __init__(self, mapping_or_function: Mapper | SpecialFunction, mapping_label = None, released=-100, pressed=100, delay=0.1, **kwargs):
        super().__init__(mapping_or_function, mapping_label, released, pressed, self.mapping_label)

        self.delay = delay

    def process(self, value):
        if value:
            if not self.map(self.pressed, self.mapping_label):
                return False

            time.sleep(self.delay)

            return self.map(self.released, self.mapping_label)
