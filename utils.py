import json
import os

def snake_to_camel(snake_string: str):
    return "".join([word.capitalize() for word in snake_string.split("_")])

def pretty_print(d: dict):
    print(json.dumps(d, indent=4, skipkeys=True))

def resolve_path(path: str | None, default: str):
    # Default path
    if path == "" or path is None:
        return resolve_path(default)
    # Absolute path
    elif os.path.isabs(path):
        return path
    # Home dir path
    elif path.startswith("~"):
        return os.path.expanduser(
            os.path.expandvars(
                path
            )
        )
    # Relative path
    else:
        return os.path.expandvars(
            os.path.join(
                os.getcwd(),
                path
            )
        )
