import json

def snake_to_camel(snake_string: str):
    return "".join([word.capitalize() for word in snake_string.split("_")])

def pretty_print(d: dict):
    print(json.dumps(d, indent=4, skipkeys=True))
