import inspect, argparse


class CommandManager:
    def __init__(self):
        self._cmds = {}
        self._parser = argparse.ArgumentParser("pyu")
        self._sub = self._parser.add_subparsers(dest="command")
        self._groups = {}

    def command(self, cmd: str, subcmd: str | None = None):
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

                p = self._groups[cmd]._sub.add_parser(subcmd, help=fn.__doc__)
                self._cmds[(cmd, subcmd)] = fn

            for name, param in inspect.signature(fn).parameters.items():
                if param.default is inspect._empty:
                    p.add_argument(name, type=param.annotation or str)
                else:
                    if param.annotation is bool:
                        p.add_argument("--"+name, default=param.default, action="store_true")
                    else:
                        p.add_argument("--"+name, nargs="?", default=param.default, type=param.annotation or str)

            return fn
        return decorator
    def process_commands(self):
        args = self._parser.parse_args()

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
