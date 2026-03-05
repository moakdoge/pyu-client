import argparse
from typing import Any
class CommandManager:
    def __init__(self):
        self._cmds = {}
        self._parser = argparse.ArgumentParser("pyu")

    def command(self, cmd: str, description: str="", author: str="") -> Any:
        def decorator(fn):
            c=Command(fn)
            self._parser.add_subparsers(dest=cmd)
            self._cmds[cmd] = c
            return c
        return decorator
    
    def process_commands(self):
        self._processed = self._parser.parse_args()
        for arg, value in self._processed.__dict__.items():
            print(arg, value)
        pass

class Command:
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)
        