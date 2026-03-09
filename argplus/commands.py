import argparse, inspect
from typing import Any
class CommandManager:#men
    def __init__(self):
        self._cmds = {}
        self._parser = argparse.ArgumentParser("pyu")
        self._cmd_parser = self._parser.add_subparsers(dest="command")
    def command(self, cmd: str, author: str="") -> Any:
        def decorator(fn):
            c=fn
            p = self._cmd_parser.add_parser(cmd, help=fn.__doc__)
            for name, param in inspect.signature(fn).parameters.items():
                if param.default is inspect._empty:
                    p.add_argument(name, type=param.annotation or str)
                else:
                    if param.annotation is bool:
                        p.add_argument("--"+name, default=param.default, action="store_true")
                    else:
                        p.add_argument("--"+name, nargs="?", default=param.default, type=param.annotation or str)
            self._cmds[cmd] = c
            return c
        return decorator
    
    def process_commands(self):
        self._processed = self._parser.parse_args()
        command = self._processed.command
        params = []
        if command in self._cmds:
            fn=self._cmds[command]
            for name, param in inspect.signature(fn).parameters.items():
                if param.name in self._processed.__dict__:
                    params.append(self._processed.__dict__[param.name])
            fn(*params)
        pass

