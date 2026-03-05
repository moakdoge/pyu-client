import argparse, requests, tempfile, zipfile, shutil, os, time,sys
from pathlib import Path
from argplus import commands
from packagemanager import packages
import logging

#handle arguments
manager = commands.CommandManager()
#global shit
site_packages = Path(next(x for x in sys.path if "packages" in x))

@manager.command("install")
def install(package: str, local: bool = False, depends: bool = True):
    '''Installs a package.'''
    result = Path(__file__).parent if local else site_packages
    logging.log(1, f"Installing package {package} to {result}")
    try:
        packages.download_package(package, result=result)
    except Exception as e:
        logging.error(f"{e}. Your command has not been executed.")
    logging.log(1, f"Downloaded {package} successfully!")

    pass


manager.process_commands()