import argparse, requests, tempfile, zipfile, shutil, os, time,sys
import json
from pathlib import Path
from argplus import commands
from packagemanager import packages, searcher
import logging

#handle arguments
manager = commands.CommandManager()
#global shit
site_packages = Path(next(x for x in sys.path if "packages" in x))

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)
@manager.command("install")
def install(package: str, local: bool = False, depends: bool = True):
    '''Installs a package.'''
    result = Path(__file__).parent if local else site_packages
    log.info(f"Installing package {package} to {result}")
    try:
        packages.download_package(package, result=result)
    except Exception as e:
        log.error(f"{e}. Your command has not been executed.")
    log.info(f"Downloaded {package} successfully!")
    pass

@manager.command("uninstall")
def uninstall(package: str, local: bool = False, keep_depends: bool = False):
    log.info('Searching for package...')
    O = (Path(os.getcwd()) if local else None)
    folder = searcher.search_package(package, O)
    if not folder:
        log.error(f"Could not find package {package}!")
        return
    metadata = (folder / "metadata.json").read_text()
    dicted = json.loads(metadata)
    _depends = dicted.get("depends", {})

    log.info(f"Removed package {folder.name}")
    shutil.rmtree(folder)
    
    if not keep_depends:
        for lib, version in _depends.items():
            fold = searcher.search_package(lib, O)
            if fold:
                shutil.rmtree(fold)
                log.info(f"Removed dependency of {fold}")

manager.process_commands()