# TODO: limit outputs to -100, 100 for all mappers
# TODO: Mapper interface
# TODO: Expo

def axis_passthrough(input, weight, min, max, center, deadband, **kwargs):
    if abs(input) <= deadband:
        return center
    elif input > 0:
        if max >= 0:
            output = (weight)/(100-deadband)*(input-deadband)+center

            if output >= 100 and max >= 100:
                return 100
            elif output >= max:
                return max
            else:
                return output
        else:
            output = (-weight)/(100-deadband)*(input-deadband)+center

            if output <= -100 and max <= -100:
                return -100
            elif output <= max:
                return max
            else:
                return output
    else:
        if min <= 0:
            output = (weight)/(100-deadband)*(input+deadband)+center

            if output <= -100 and min <= -100:
                return -100
            elif output <= min:
                return min
            else:
                return output
        else:
            output = (-weight)/(100-deadband)*(input+deadband)+center

            if output >= 100 and min >= 100:
                return 100
            elif output >= min:
                return min
            else:
                return output

def axis_passthrough_absolute_weight(input, weight, min, max, center, deadband, **kwargs):
    if abs(input) <= deadband:
        return center
    elif input > 0:
        if max >= 0:
            output = (weight-center)/(100-deadband)*(input-deadband)+center

            if output >= 100 and max >= 100:
                return 100
            elif output >= max:
                return max
            else:
                return output
        else:
            output = (-weight-center)/(100-deadband)*(input-deadband)+center

            if output <= -100 and max <= -100:
                return -100
            elif output <= max:
                return max
            else:
                return output
    else:
        if min <= 0:
            output = (center+weight)/(100-deadband)*(input+deadband)+center

            if output <= -100 and min <= -100:
                return -100
            elif output <= min:
                return min
            else:
                return output
        else:
            output = (center-weight)/(100-deadband)*(input+deadband)+center

            if output >= 100 and min >= 100:
                return 100
            elif output >= min:
                return min
            else:
                return output


def axis_passthrough_scaled_weight(input, min, max, center, deadband, **kwargs):
    if abs(input) <= deadband:
        return center
    elif input > 0:
        output = (max-center)/(100-deadband)*(input-deadband)+center

        if max >= 0 and output >= 100:
            return 100
        elif max < 0 and output <= -100:
            return -100
        else:
            return output
    else:
        output = (center-min)/(100-deadband)*(input+deadband)+center

        if min <= 0 and output <= -100:
            return -100
        elif min > 0 or output >= 100:
            return 100
        else:
            return output


def button_momentary(input, pressed, released, **kwargs):
    return pressed if input else released

def map_to_channel_range(output):
    return int(output*10)
