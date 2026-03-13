from dataclasses import dataclass
import inspect, argparse
from pathlib import Path
import atexit
import sys
from typing import Annotated, Any, get_args, get_origin, get_type_hints
from . import ctx as ct
from . import custom
import os


class CommandException(BaseException):
    def __init__(self, status_code: int, status_message: str) -> None:
        self.code = status_code
        self.message = status_message
        super().__init__(f"Command raised exception (Status code {status_code}): {status_message}")

@dataclass
class CommandGroup:
    name: str
    _cmd: Any
    def register(self, sub_command: str, **kwargs):
        return self._cmd(cmd=self.name, subcmd=sub_command, **kwargs)
from types import SimpleNamespace
class CommandManager:
    def __init__(self, name: str | None = None, description: str = ""):
        os.environ["CommandManagerCreated"] = "1"
        self._cmds = {}
        __n = name if name is not None else Path(__file__).stem
        self._parser = argparse.ArgumentParser(__n, description=description,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self._sub = self._parser.add_subparsers(dest="command")
        self._groups = {}
        self._before = []
        self._after = []
        self.globals = SimpleNamespace()
        self._global_parser =  argparse.ArgumentParser(add_help=False)
        self._global_names = set()
        
        #manually adding the ability to add --path
        self._global_parser.add_argument(f"--path", type=Path)
        self.cwd: Path
        
    def group(self, group_name: str) -> CommandGroup:
        new = CommandGroup(group_name, self.register)
        return new

    def add_global(self, argument_name: str, default:Any= None, *args, **kwargs):
        self._global_parser.add_argument(f"--{argument_name}", default=default, *args, **kwargs)
        self._global_names.add(argument_name)

    def register(self, cmd: str, subcmd: str | None = None, aliases: list[str] | None = None, private: bool = False):
        def decorator(fn):
            
            if subcmd is None:
                # top level command
                p = self._sub.add_parser(cmd, help=fn.__doc__, parents=[self._global_parser])
                self._cmds[cmd] = fn

            else:
                # grouped command
                if cmd not in self._groups:
                    gp = self._sub.add_parser(cmd)
                    gp._sub = gp.add_subparsers(dest="subcommand") # type: ignore
                    self._groups[cmd] = gp

                
                p = self._groups[cmd]._sub.add_parser(
                    subcmd,
                    help=fn.__doc__,
                    aliases=aliases or [],
                    parents=[self._global_parser]
                )
                self._cmds[(cmd, subcmd)] = fn
                if aliases:
                    for arg in aliases:
                        self._cmds[(cmd, arg)] = fn
                    

            for name, param in inspect.signature(fn).parameters.items():
                anno = param.annotation 
                _h=f"(default: {str(param.default) if param.default is not inspect._empty else None})"if not private else argparse.SUPPRESS
                _real = anno
                if get_origin(anno) is Annotated:
                    base_type, *other = get_args(anno)
                    anno = base_type
                    if isinstance(other[0], custom.BaseAnnotation):
                        _h = f"{other[0].description} [{anno}] {_h}"
                        _real = other[0]
                    else:
                        _h = f"{other[0]} {_h}"
                if private:
                    _h = argparse.SUPPRESS
                if anno is inspect._empty or anno is None:
                    anno = Any
                if param.default is inspect._empty:
                    p.add_argument(name, type=_real if _real is not Any else str, help=_h)
                else:
                    if name in self._global_names:
                        continue
                    if param.annotation is bool:
                        if param.default:
                            p.add_argument("--no-"+name, action="store_false", dest=name, default=param.default, help=_h)
                        else:
                            p.add_argument("--"+name, action="store_true", default=param.default, help=_h)
                    else:
                        p.add_argument("--"+name, default=param.default, type=_real, help=_h, metavar=getattr(anno, "__name__", None) or (anno.__qualname__))

            return fn
        return decorator
    def process_commands(self, argv: list | None = None) -> int:
        args = self._parser.parse_args(argv or sys.argv[1:])
        self.cwd = args.path or Path(os.getcwd()).resolve()
        os.environ["CommandManagerCalled"] = "1"
        for name in self._global_names:
            setattr(self.globals, name, getattr(args, name))
            delattr(args, name)

        if hasattr(args, "subcommand") and args.subcommand:
            fn = self._cmds.get((args.command, args.subcommand))
        else:
            if args.command in self._groups and getattr(args, "subcommand", None) is None:
                self._groups[args.command].print_help()
                return 1
            fn = self._cmds.get(args.command)

        if fn:
            params = []
            for name in inspect.signature(fn).parameters:
                params.append(getattr(args, name))
            try:
                __back = fn
                _ = fn
                ctx = ct.CommandContext(command=args.command, args=args, func=fn)
                for before in self._before:
                    if hasattr(before, "_cmds"):
                        if len(before._cmds) > 0:
                            if args.command not in before._cmds and (args.command, getattr(args, "subcommand", None)) not in before._cmds:
                                continue
                    returned = before(ctx)
                    if returned is not None:
                        _ = returned
                try:
                    if _ != fn:
                        r= _(*params)
                    else:
                        r= fn(*params)
                except CommandException as e:
                    r = e.code
                try:
                    if r is None:
                        ctx.return_code = 0
                    else:
                        ctx.return_code= int(r)
                except ValueError:
                    raise ValueError(f"Return must be either None or int!")

                
                for after in self._after:
                    
                    
                    if hasattr(after, "_cmds") and after._cmds and len(after._cmds) > 0:
                        if args.command not in after._cmds and (args.command, getattr(args, "subcommand", None)) not in after._cmds:
                            continue

                    aftered = after(ctx)

                return ctx.return_code
            
            except KeyboardInterrupt:
                pass

        else:
            if args.command in self._groups and getattr(args, "subcommand", None) is None:
                self._groups[args.command].print_help()
            else:
                self._parser.print_help()
        return 1
    
    def run(self, *commands: str) -> int:
        return self.process_commands(list(commands)) 
    
    def get(self, command: str | tuple[str, str]):
        if command in self._cmds:
            return self._cmds[command]
        return None 

    def before_command(self, *commands: str):
        def decorator(fn):
            fn._cmds = commands
            self._before.append(fn)
            return fn
        return decorator
    
    def after_command(self, *commands: str):
        def decorator(fn):
            fn._cmds = commands
            self._after.append(fn)
            return fn
        return decorator

    @property
    def commands(self) -> list:
        return list(self._cmds.values())
    
    def __len__(self):
        return len(self.commands)
    
    def __repr__(self) -> str:
        return f"<CommandManager name='{self._parser.prog}', commands={len(self.commands)}>"
    
    def __str__(self) -> str:
        proper = []
        for _cmd, _val in self._cmds.items():
            if isinstance(_cmd, tuple):
                proper.append(f"{_cmd[0]} {_cmd[1]}")
            else:
                proper.append(f"{_cmd}")
        return f"<CommandManager {self._parser.prog}({", ".join(proper)})>"