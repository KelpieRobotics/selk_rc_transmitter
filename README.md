# selk_rc_transmitter

Linux gamepad controls transmitter. Requires [selk_rc_receiver](https://github.com/KelpieRobotics/selk_rc_receiver) to receive and output as an SBUS receiver.

## Architecture

A Gamepad consists of many inputs which fall into one of the 2 caterogies, an axis or a button. Axes are analogue inputs with ranges from -1 to 1, while buttons are discrete input returning True when pressed and False when released.

When a Input changes on any of the axes or buttons on the Gamepad, an event is generated, with the type of input, its label (either the input number or its friendly name) and the new value of the input. Then the new value will be processed, mapped and then finally output.

```
           *********      **********      **********
Value ---> * Input * ---> * Mapper * ---> * Output * ---> transmission
           *********      **********      **********
```

Input - This step takes the raw value from the controller, and user-defined parameters to scale it to [-100,100] range.

Mapper - this step takes the scaled value and calculates the appropriate output

Output - this step takes the final value transmits it

This program uses a -100 to 100 range for all purposes and all inputs will be mapped to this range. A value must fall into this range or else it will be rounded to the nearest limit. The value may be an int or a float, however, only a single decimal precision will be transmitted, rounding with the floor function.

## FIXME: Config

### Inputs

#### Axis

##### `mode`
Currently mode can be one of the following:

* ###### `normal`

This mode should be used in most cases. Input is passthrough, with certain modifications to the signal. See the descriptions of other params to determine their function.

Example

<!-- FIXME: New config schema -->
```yaml
mappings:
  axis:
    "passthrough":
      channel: None
      mode: passthrough
      weight: 200
      min: -75
      max: 50
      center: 0
      deadband: 0
```

![passthrough.png](images/passthrough.png)

* ###### `absolute_weight`

Similar to `normal`, however, the `weight` param has a different behaviour when `center` is not zero.

In `normal` mode, the `weight` will be offset by the `center` value. This is useful when you want to move the center point of the output but keep the same rate of change for a given change of input.

However, in `absolute_weight` mode, the weight determines to what value output is extrapolated at 100 input when `max` is sufficiently large. That means when `center` is not zero, function still pass through the (100, `weight`) point (notice the slop of the function may be different if `max` != -`min`).

Example

<!-- FIXME: New config schema -->
```yaml
mappings:
  axis:
    "passthrough":
      channel: None
      mode: passthrough
      weight: 100
      min: -50
      max: 100
      center: 50
      deadband: 0

    "passthrough_absolute_weight":
      channel: None
      mode: "passthrough_absolute_weight"
      weight: 100
      min: -50
      max: 100
      center: 50
      deadband: 0

```

![passthrough_vs_passthrough_absolute_weight.png](images/passthrough_vs_passthrough_absolute_weight.png)

* ###### `scaled_weight`

Similar to `passthrough` with a different behaviour around limits.

In `nornmal` mode, the `weight` param determines the slop of the function, with `min` and `max` parameters creating a hard cap on the value.

When using `scaled_weight`, the `weight` param is ignored, and the slope is determined by the `min` and `max` params. The function will pass through both (-100, `min`) and (100, `max`) points. It consists of 2 linear segments from (0, `center`) to these points.

Example

<!-- FIXME: New config schema -->
```yaml
mappings:
  axis:
    "passthrough":
      channel: None
      mode: passthrough
      weight: 400
      min: -125
      max: 25
      center: 0
      deadband: 0

    "passthrough_scaled_weight":
      channel: None
      mode: "passthrough_scaled_weight"
      weight: 400 # does nothing
      min: -125
      max: 25
      center: 0
      deadband: 0
```

![passthrough_vs_passthrough_scaled_weight.png](images/passthrough_vs_passthrough_scaled_weight.png)

##### `weight`

The slope of the linear function in terms of percentage (`weight: 100` corresponds to the equivalent of y=x, while `weight: 200` is y=2x).

Note: Depending on the `mode` and other params (such as `deadband`) the actual slope may be differ from the weight parameter. Consult this documentation and visualize your config, to better understand how it works.

Examples

<!-- FIXME: New config schema -->
```yaml
mappings:
  axis:
    "passthrough (weight = 100)":
      channel: None
      mode: passthrough
      weight: 100
      min: -100
      max: 100
      center: 0
      deadband: 0

    "passthrough (weight = 200)":
      channel: None
      mode: passthrough
      weight: 200
      min: -100
      max: 100
      center: 0
      deadband: 0
```

![passthrough_weight.png](images/passthrough_weight.png)

##### `min`

The output limit when input is negative.

##### `max`

The output limit when input is positive.

##### `center`

They y-axis offset. This is the output when input is equal to 0 (center of the stick)

##### `deadband`

Maximum deviation from 0 input, where the stick is "dead" (should be reading 0). This parameter can be used to correct for stick drift.

Example

<!-- FIXME: New config schema -->
```yaml
mappings:
  axis:
    "passthrough":
      channel: None
      mode: passthrough
      weight: 100
      min: -100
      max: 100
      center: 0
      deadband: 10
```
![passthrough_deadband.png](images/passthrough_deadband.png)


##### Tips and Tricks
* ###### Invert
You can invert any input but swapping around `min` and `max` params.

Note: Do not invert weight, as inverting weight as well will revert change the slope back the original value.

Example

<!-- FIXME: New config schema -->
```yaml
mappings:
  axis:
    "passthrough":
      channel: None
      mode: passthrough
      weight: 200
      min: -75
      max: 50
      center: 0
      deadband: 0

    "passthrough inverted":
      channel: None
      mode: passthrough
      weight: 200
      min: 50
      max: -75
      center: 0
      deadband: 0
```

![passthrough_inverted.png](images/passthrough_inverted.png)

* ###### Y-axis Symmetry and Abs

The sign of either `min` or `max` also decided the sign on the slope. We can create an abs function by making the `min` param positive.

Example

<!-- FIXME: New config schema -->
```yaml
mappings:
  axis:
    "passthrough":
      channel: None
      mode: passthrough
      weight: 100
      min: -100
      max: 100
      center: 0
      deadband: 0

    "|passthrough|":
      channel: None
      mode: passthrough
      weight: 100
      min: 100
      max: 100
      center: 0
      deadband: 0
```

![passthrough_abs.png](images/passthrough_abs.png)
