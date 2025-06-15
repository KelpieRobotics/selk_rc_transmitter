from custom_types import (
    Mapper,
    SpecialFunction,
    Outputter,
    AxisInputConfig,
    ButtonInputConfig,
    MappingConfig,
    SpecialFunctionConfig,
    SpecialFunctionMapping,
    ImageStitchSpecialFunctionConfig,
    ImageStitchSpecialFunctionMapping,
    OutputConfig,
    Config,
    Inputs
)
import inputters
import mappers
import special_functions
import outputters
from utils import snake_to_camel

from typing import Dict
import yaml
from copy import deepcopy


default_axis_input_config: AxisInputConfig = {
    "mapping": None,
    "mode": "normal",
    "min": -100,
    "max": 100,
    "weight": 100,
    "center": 0,
    "deadband": 0,
    "neutral": 0
}

default_button_input_config: ButtonInputConfig = {
    "mapping": None,
    "mode": "normal",
    "released": -100,
    "pressed": 100
}

default_mapping_config: MappingConfig = {
    "output": None,
    "mode": "passthrough",
    "min": -100,
    "max": 100,
    "center": 0,
    "speed": 20
}

default_image_stitch_config: ImageStitchSpecialFunctionConfig = {
    "mappings": None,
    "output_dir": "panorama",
    "port": 5702
}

default_image_stitch_mapping_config: ImageStitchSpecialFunctionMapping = {
    "mapping": None,
    "min": -100,
    "max": 100,
    "step": 20
}

default_output_config: OutputConfig = {
    "type": "selk_udp",
    "target": {"host": "192.168.137.255", "port": 5005}
}


# TODO: Proper type and required member checking (Pydantic?)
# TODO: Verify labels
def load_config(config_filename):
    with open(config_filename, 'r') as config_file:
        config: Config = yaml.safe_load(config_file)

        print("Loaded config")

    inputs: Inputs = {"axes": {}, "buttons": {}}
    mappings: Dict[str, Mapper] = {}
    functions: Dict[str, SpecialFunction] = {}
    outputs: Dict[str, Outputter] = {}

    if "outputs" in config:
        outputs_keys = set(config["outputs"].keys())
        for output in outputs_keys:
            if "type" in config["outputs"][output] and config["outputs"][output]["type"] not in outputters.outputters:
                print(config["outputs"][output]["type"], "is not a valid type. Discarding output...")

                del config["outputs"][output]
                continue

            for param in default_output_config:
                if param not in config["outputs"][output]:
                    config["outputs"][output][param] = default_output_config[param]

            output_config = deepcopy(config["outputs"][output])
            output_config.pop("type")

            outputs[str(output)] = getattr(outputters, snake_to_camel(config["outputs"][output]["type"])+"Outputter")(**output_config)

    if "mappings" in config:
        mappings_keys = set(config["mappings"].keys())
        for mapping in mappings_keys:
            if type(config["mappings"][mapping]) is str or type(config["mappings"][mapping]) is int:
                if config["mappings"][mapping] not in outputs:
                    print(config["mappings"][mapping], "output does not exist. Discarding mapping...")

                    del config["mappings"][mapping]
                    continue

                output_name = config["mappings"][mapping]
                config["mappings"][mapping] = deepcopy(default_mapping_config)
                config["mappings"][mapping]["output"] = output_name

            elif type(config["mappings"][mapping]) is MappingConfig:
                if config["mappings"][mapping]["output"] is None:
                    print(mapping, "mapping does not have a output specified. Discarding mapping...")

                    del config["mappings"][mapping]
                    continue

                if config["mappings"][mapping]["output"] not in outputs or (config["mappings"][mapping]["output"] is str and config["mappings"][mapping]["output"].split(".")[0] not in outputs):
                    print(config["mappings"][mapping]["output"], "output does not exist. Discarding mapping...")

                    del config["mappings"][mapping]
                    continue

                if "type" in config["mappings"][mapping] and config["mappings"][mapping]["type"] not in mappers.mappers:
                    print(config["mappings"][mapping]["type"], "is not a valid type. Discarding mapping...")

                    del config["mappings"][mapping]
                    continue

                for param in default_mapping_config:
                    if param not in config["mappings"][mapping]:
                        config["mappings"][mapping][param] = default_mapping_config[param]

            mapping_config = deepcopy(config["mappings"][mapping])
            output_str = str(mapping_config.pop("output")).split(".")
            mapping_config.pop("type")

            mappings[str(mapping)] = getattr(mappers, snake_to_camel(config["mappings"][mapping]["type"])+"Mapper")(outputs[output_str[0]], ".".join(output_str[1:]) if len(output_str) > 1 else None, **mapping_config)

    if "special_functions" in config:
        special_functions_keys = set(config["special_functions"].keys())
        for special_function in special_functions_keys:
            if special_function in mappings:
                print("A mapping and a special function can't both have the same name ", special_function,". Discarding special function...", sep="")

                del config["special_functions"][special_function]
                continue

            if config["special_functions"][special_function]["function"] not in special_functions.special_functions:
                print(config["special_functions"][special_function]["function"], "is not a valid function. Discarding special function...")

                del config["special_functions"][special_function]
                continue

            special_function_config = deepcopy(config["special_functions"][special_function])
            if "mappings" in special_function_config:
                parse_sucessful = True
                for mapping in special_function_config["mappings"]:
                    if special_function_config["mappings"][mapping]["mapping"] not in mappings:
                        print(special_function_config["mappings"][mapping]["mapping"], "mapping doesn't exist.")
                        parse_sucessful = False
                        break

                    special_function_config["mappings"][mapping]["mapping"] = mappings[special_function_config["mappings"][mapping]["mapping"]]

                    default_mapping_config: SpecialFunctionMapping = deepcopy(globals()["default_"+special_function_config["function"]+"_mapping_config"])
                    for param in default_mapping_config:
                        if param not in special_function_config["mappings"][mapping]:
                            special_function_config["mappings"][mapping][param] = default_mapping_config[param]


                if not parse_sucessful:
                    print("An error occured while parsing special_function. Discarding special function...")

                    del config["special_functions"][special_function]
                    continue

            default_config = deepcopy(globals()["default_"+special_function_config["function"]+"_config"])
            for param in default_config:
                if param not in config["special_functions"][special_function]:
                    config["special_functions"][special_function][param] = default_config[param]

            special_function_config.pop("function")

            functions[special_function] = getattr(special_functions, snake_to_camel(config["special_functions"][special_function]["function"])+"SpecialFunction")(**special_function_config)

    if "inputs" in config:
        # Axis inputs
        if "axes" in config["inputs"]:
            axes_keys = set(config["inputs"]["axes"].keys())
            for axis in axes_keys:
                if type(config["inputs"]["axes"][axis]) is str or type(config["inputs"]["axes"][axis]) is int:
                    axis_mapping = config["inputs"]["axes"][axis]

                    config["inputs"]["axes"][axis] = deepcopy(default_axis_input_config)
                    config["inputs"]["axes"][axis]["mapping"] = axis_mapping

                elif type(config["inputs"]["axes"][axis]) is AxisInputConfig:
                    if config["inputs"]["axes"][axis]["mapping"] is None:
                        print(axis, "does not have a mapping specified. Discarding axis...")

                        del config["inputs"]["axes"][axis]
                        continue

                    if config["inputs"]["axes"][axis]["mapping"] in mappings or str(config["inputs"]["axes"][axis]["mapping"]).split(".")[0] in mappings:
                        pass
                    elif config["inputs"]["axes"][axis]["mapping"] in functions or str(config["inputs"]["axes"][axis]["mapping"]).split(".")[0] in functions:
                        pass
                    else:
                        print(config["inputs"]["axes"][axis]["mapping"], "mapping does not exist. Discarding axis...")

                        del config["inputs"]["axes"][axis]
                        continue

                    if "mode" in config["inputs"]["axes"][axis] and config["inputs"]["axes"][axis]["mode"] not in inputters.axis_inputters:
                        print(config["inputs"]["axes"][axis]["mode"], "is not a valid mode. Discarding axis...")

                        del config["inputs"]["axes"][axis]
                        continue

                    # Substitue defaults for missing params
                    for param in default_axis_input_config:
                        if param not in config["inputs"]["axes"][axis]:
                            config["inputs"]["axes"][axis][param] = default_axis_input_config[param]

                axis_config = deepcopy(config["inputs"]["axes"][axis])
                mapping_str = str(axis_config.pop("mapping")).split(".")
                axis_config.pop("mode")

                mapping_or_function = mappings[mapping_str[0]] if mapping_str[0] in mappings else functions[mapping_str[0]]

                inputs["axes"][axis] = getattr(inputters, snake_to_camel(config["inputs"]["axes"][axis]["mode"])+"AxisInputter")(mapping_or_function, ".".join(mapping_str[1:]) if len(mapping_str) > 1 else None, **axis_config)


        # Button inputs
        if "buttons" in config["inputs"]:
            buttons_keys = config["inputs"]["buttons"].keys()
            for button in buttons_keys:
                if type(config["inputs"]["buttons"][button]) is str or type(config["inputs"]["buttons"][button]) is int:
                    button_mapping = config["inputs"]["buttons"][button]

                    config["inputs"]["buttons"][button] = deepcopy(default_button_input_config)
                    config["inputs"]["buttons"][button]["mapping"] = button_mapping
                elif type(config["inputs"]["buttons"][button]) is ButtonInputConfig:
                    if "mapping" not in config["inputs"]["buttons"][button] or config["inputs"]["buttons"][button]["mapping"] is None:
                        print(button, "does not have a mapping specified. Discarding button...")

                        del config["inputs"]["buttons"][button]
                        continue

                    if config["inputs"]["buttons"][button]["mapping"] in mappings or str(config["inputs"]["buttons"][button]["mapping"]).split(".")[0] in mappings:
                        pass
                    elif config["inputs"]["buttons"][button]["mapping"] in functions or str(config["inputs"]["buttons"][button]["mapping"]).split(".")[0] in functions:
                        pass
                    else:
                        print(config["inputs"]["buttons"][button]["mapping"], "mapping does not exist. Discarding button...")

                        del config["inputs"]["buttons"][button]
                        continue

                    if "mode" in config["inputs"]["buttons"][button] and config["inputs"]["buttons"][button]["mode"] not in inputters.button_inputters:
                        print(config["inputs"]["axes"][button]["mode"], "is not a valid mode. Discarding button...")

                        del config["inputs"]["axes"][button]
                        continue

                    # Substitue defaults for missing params
                    for param in default_button_input_config:
                        if param not in config["inputs"]["buttons"][button]:
                            config["inputs"]["buttons"][button][param] = default_button_input_config[param]

                button_config = deepcopy(config["inputs"]["buttons"][button])
                mapping_str = str(button_config.pop("mapping")).split(".")
                button_config.pop("mode")

                mapping_or_function = mappings[mapping_str[0]] if mapping_str[0] in mappings else functions[mapping_str[0]]

                inputs["buttons"][button] = getattr(inputters, snake_to_camel(config["inputs"]["buttons"][button]["mode"])+"ButtonInputter")(mapping_or_function, ".".join(mapping_str[1:]) if len(mapping_str) > 1 else None, **button_config)

    return config, inputs, mappings, functions, outputs
