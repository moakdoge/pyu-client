import argparse, requests, tempfile, zipfile, shutil, os, time,sys
from pathlib import Path
from argplus import commands

URL = "http://127.0.0.1:5000"

#handle arguments
manager = commands.CommandManager()
#global shit
site_packages = Path(next(x for x in sys.path if "packages" in x))
#package = args.package
#result = Path(__file__).parent if args.local else site_packages

@manager.command("cmd")
def _install():
    print("inst")
    pass


manager.process_commands()