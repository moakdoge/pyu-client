import sys


def ask(prompt: str = "", preferred: bool = True) -> bool:
    allowed_yess = ["yes", "y", "true"]
    allowed_no = ["no", "n", "false"]
    _x = ""

    while _x.lower() not in allowed_yess and _x.lower() not in allowed_no:
        _x = input(f"{prompt} ({"Y" if preferred else "y"}/{"N" if not preferred else "n"})> ")
        if _x == "":
            return preferred

    return (_x.lower() in allowed_yess)
