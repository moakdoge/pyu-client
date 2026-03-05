import argparse, requests, tempfile, zipfile, shutil, os, time,sys
from pathlib import Path
from argplus import commands

URL = "http://127.0.0.1:5000"

#handle arguments
manager = commands.CommandManager()
#global shit
site_packages = Path(next(x for x in sys.path if "packages" in x))

@manager.command("install")
def _install(package: str, local: bool = False):
    '''Installs a package.'''
    result = Path(__file__).parent if local else site_packages
    print("installing",package,"result",result)
    pass


manager.process_commands()