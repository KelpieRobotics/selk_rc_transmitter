import configs
import mappers

import matplotlib.pyplot as plt
import numpy as np

# TODO: argparse

def create_subplot(subplot_axes, x_values, axis, axis_config):
    y_values = [getattr(mappers, "axis_"+axis_config["mode"])(x, **axis_config) for x in x_values]

    subplot_axes.plot(x_values, y_values, 'b-', linewidth=2)
    subplot_axes.set_title(axis)
    subplot_axes.set_xlabel('input')
    subplot_axes.set_ylabel('output')
    subplot_axes.grid(True, alpha=0.3)

    subplot_axes.axhline(y=0, color='black', linewidth=1.5, alpha=0.8)
    subplot_axes.axvline(x=0, color='black', linewidth=1.5, alpha=0.8)

    subplot_axes.set_xlim(-100, 100)
    subplot_axes.set_ylim(-100, 100)

config = configs.load_config('config.yaml')

fig, axes = plt.subplots(len(config["mappings"]["axis"]), 1, figsize=(7, 6*len(config["mappings"]["axis"])))

# Create x values in the domain [-1, 1]
x_values = np.linspace(-100, 100, 1000)

if len(config["mappings"]["axis"]) >= 1:
    if len(config["mappings"]["axis"]) > 1:
        i = 0
        for axis in config["mappings"]["axis"]:
            create_subplot(axes[i], x_values, axis, config["mappings"]["axis"][axis])

            i += 1
    else:
        axis = set(config["mappings"]["axis"].keys()).pop()
        create_subplot(axes, x_values, axis, config["mappings"]["axis"][axis])

    plt.tight_layout()
    plt.show()
