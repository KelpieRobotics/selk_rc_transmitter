import yaml

default_axis_config = {
    "mode": "passthrough_scale",
    "min": -100,
    "max": 100,
    "weight": 100,
    "center": 0,
    "deadband": 0
}

default_button_config = {
    "mode": "momentary",
    "released": -100,
    "pressed": 100
}

axis_modes = {
    "passthrough_scale",
    "passthrough_cap",
    "passthrough_center_cap",
    # TODO: "relative"
}

button_modes = {
    "momentary",
    # TODO: "toggle",
    # TODO: "image_stich"
}

# TODO: remove static type checking with a type check object
def load_config(config_filename, available_channels = None):
    with open(config_filename, 'r') as config_file:
        config = yaml.safe_load(config_file)

        print("Loaded config")

        # Axis mappings
        if "axis" in config["mappings"] and type(config["mappings"]["axis"]) is dict:
            axis_keys = set(config["mappings"]["axis"].keys())
            for input in axis_keys:
                if type(config["mappings"]["axis"][input]) is str:
                    input_channel = config["mappings"]["axis"][input]

                    config["mappings"]["axis"][input] = default_axis_config.copy()
                    config["mappings"]["axis"][input]["channel"] = input_channel
                elif type(config["mappings"]["axis"][input]) is dict:
                    if "channel" not in config["mappings"]["axis"][input]:
                        print(input, "does not have a channel specified. Ignoring...")

                        del config["mappings"]["axis"][input]
                        continue

                    elif available_channels is not None and config["mappings"]["axis"][input]["channel"] not in available_channels:
                        print(config["mappings"]["axis"][input]["channel"], "is not a valid channel. Ignoring...")

                        del config["mappings"]["axis"][input]
                        continue

                    # Substitue defaults for missing params
                    for param in default_axis_config:
                        if param not in config["mappings"]["axis"][input]:
                            config["mappings"]["axis"][input][param] = default_axis_config[param]

                    # TODO: mode validation

        # Button mappings
        if "button" in config["mappings"] and type(config["mappings"]["button"]) is dict:
            button_keys = config["mappings"]["button"].keys()
            for input in button_keys:
                if type(config["mappings"]["button"][input]) is str:
                    input_channel = config["mappings"]["button"][input]

                    config["mappings"]["button"][input] = default_button_config.copy()
                    config["mappings"]["button"][input]["channel"] = input_channel
                elif type(config["mappings"]["button"][input]) is dict:
                    if "channel" not in config["mappings"]["button"][input]:
                        print(input, "does not have a channel specified. Ignoring...")

                        del config["mappings"]["button"][input]
                        continue

                    elif available_channels is not None and config["mappings"]["button"][input]["channel"] not in available_channels:
                        print(config["mappings"]["button"][input]["channel"], "is not a valid channel. Ignoring...")

                        del config["mappings"]["button"][input]
                        continue

                    # Substitue defaults for missing params
                    for param in default_button_config:
                        if param not in config["mappings"]["button"][input]:
                            config["mappings"]["button"][input][param] = default_button_config[param]

                    # TODO: mode validation

    return config
