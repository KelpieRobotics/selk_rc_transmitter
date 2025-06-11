import configs
import inputters

import matplotlib.pyplot as plt
import numpy as np

# TODO: argparse

def create_subplot(subplot_axes, x_values, axis, input: inputters.AxisInputter):
    y_values = [input.transform(x) for x in x_values]

    subplot_axes.plot(x_values, y_values, 'b-', linewidth=2)
    subplot_axes.set_title(axis)
    subplot_axes.set_xlabel('input')
    subplot_axes.set_ylabel('output')
    subplot_axes.grid(True, alpha=0.3)

    subplot_axes.axhline(y=0, color='black', linewidth=1.5, alpha=0.8)
    subplot_axes.axvline(x=0, color='black', linewidth=1.5, alpha=0.8)

    subplot_axes.set_xlim(-1, 1)
    subplot_axes.set_ylim(-100, 100)

inputs = configs.load_config('config.yaml')[1]

fig, axes = plt.subplots(len(inputs["axes"]), 1, figsize=(7, 6*len(inputs["axes"])))

# Create x values in the domain [-1, 1]
x_values = np.linspace(-1, 1, 1000)

if len(inputs["axes"]) >= 1:
    if len(inputs["axes"]) > 1:
        i = 0
        for axis in inputs["axes"]:
            create_subplot(axes[i], x_values, axis, inputs["axes"][axis])

            i += 1
    else:
        axis = set(inputs["axes"].keys()).pop()
        create_subplot(axes, x_values, axis, inputs["axes"][axis])

    plt.tight_layout()
    plt.show()
