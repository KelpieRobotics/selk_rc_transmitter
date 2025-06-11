import configs
from utils import pretty_print

from Gamepad import Gamepad

import time


# TODO: argparse
# TODO: asyncio



def reset_inputs():
    for axis in inputs["axes"]:
        inputs["axes"][axis].process(inputs["axes"][axis].neutral)

    for button in inputs["buttons"]:
        inputs["buttons"][button].process(False)


if __name__ == "__main__":
    config, inputs, mappings, outputs = configs.load_config('config.yaml') # TODO: Config command-line argument

    # print("Config")
    # pretty_print(config)
    # print()

    # print("Inputs")
    # pretty_print({"axes": {axis: str(inputs["axes"][axis]) for axis in inputs["axes"].keys()}, "buttons": {button: str(inputs["buttons"][button]) for button in inputs["buttons"].keys()}})
    # print()

    # print("Mappings")
    # pretty_print({mapping: str(mappings[mapping]) for mapping in mappings})
    # print()

    # print("Outputs")
    # pretty_print({output: str(outputs[output]) for output in outputs})
    # print()


    reset_inputs()

    while not Gamepad.available():
        print("Gamepad not detected. Retrying in 3 seconds...")
        time.sleep(3)

    gamepad = getattr(Gamepad, config["gamepad"])()
    print("Gamepad connected")

    try:
        while True:
            eventType, input, value = gamepad.getNextEvent()

            # print(f"Input Event - Type: {eventType}, Control: {input}, Value: {value}")

            if eventType == "AXIS" and input in inputs["axes"]:
                inputs["axes"][input].process(value)

            elif eventType == "BUTTON" and input in inputs["buttons"]:
                inputs["buttons"][input].process(value)

            # else:
            #     print(f"[Unmapped] Input '{input}' of type '{eventType}' is not mapped.")


    except BaseException as e:
        print(f"[Exception] {e}")
        reset_inputs()

