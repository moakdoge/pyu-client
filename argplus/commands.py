import inspect, argparse
from pathlib import Path
import atexit
import os


class CommandManager:
    def __init__(self, name: str | None = None, description: str = ""):
        os.environ["CommandManagerCreated"] = "1"
        self._cmds = {}
        __n = name if name is not None else Path(__file__).stem
        self._parser = argparse.ArgumentParser(__n, description=description,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self._sub = self._parser.add_subparsers(dest="command")
        self._groups = {}

    
    
    def command(self, cmd: str, subcmd: str | None = None, aliases: list[str] | None = None):
        def decorator(fn):

            if subcmd is None:
                # top level command
                p = self._sub.add_parser(cmd, help=fn.__doc__)
                self._cmds[cmd] = fn

            else:
                # grouped command
                if cmd not in self._groups:
                    gp = self._sub.add_parser(cmd)
                    gp._sub = gp.add_subparsers(dest="subcommand")
                    self._groups[cmd] = gp

                p = self._groups[cmd]._sub.add_parser(subcmd, help=fn.__doc__, aliases=aliases or [])
                self._cmds[(cmd, subcmd)] = fn
                if aliases:
                    for arg in aliases:
                        self._cmds[(cmd, arg)] = fn
                    

            for name, param in inspect.signature(fn).parameters.items():
                anno = param.annotation 
                if anno is inspect._empty or anno is None:
                    anno = str
                if param.default is inspect._empty:
                    p.add_argument(name, type=anno)
                else:
                    if param.annotation is bool:
                        if param.default:
                            p.add_argument("--no-"+name, action="store_false", dest=name, default=param.default, help=f"(default: {str(param.default)})")
                        else:
                            p.add_argument("--"+name, action="store_true", default=param.default, help=f"(default: {str(param.default)})")
                    else:
                        p.add_argument("--"+name, default=param.default, type=anno, help=f"(default: {str(param.default)})")

            return fn
        return decorator
    def process_commands(self):
        args = self._parser.parse_args()
        os.environ["CommandManagerCalled"] = "1"
        if hasattr(args, "subcommand") and args.subcommand:
            fn = self._cmds.get((args.command, args.subcommand))
        else:
            if args.command in self._groups and getattr(args, "subcommand", None) is None:
                self._groups[args.command].print_help()
                return
            fn = self._cmds.get(args.command)

        if fn:
            params = []
            for name in inspect.signature(fn).parameters:
                params.append(getattr(args, name))
            try:
                fn(*params)
            except KeyboardInterrupt:
                pass
        else:
            if args.command in self._groups and getattr(args, "subcommand", None) is None:
                self._groups[args.command].print_help()
            else:
                self._parser.print_help()
                
