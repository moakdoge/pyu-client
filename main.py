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

@manager.command("list")
def list_packages():
    packs = searcher.get_installed()
    lines = [f"Total packages installed: {len(packs)}", "--------------------"]
    for package, data in packs.items():
        lines.append(f"{package} - {data["author"]}")
    log.info("\n".join(lines))

@manager.command("clean")
def clean(confirm: bool = False):
    if not confirm:
        log.warning("clean will wipe every single package installed. If this is what you want, rerun this command passing --confirm")
    pack = searcher.get_installed()
    for package, data in pack.items():
        packages.remove_package(package)
        log.info(f"Removed package {package}")
@manager.command("uninstall")
def uninstall(package: str, local: bool = False,force: bool = False, keep_depends: bool = False):
    '''uninstalls a package'''
    log.info('Searching for package...')
    O = (Path(os.getcwd()) if local else None)
    folder = searcher.search_package(package, O)
    if not folder:
        log.error(f"Could not find package {package}!")
        return
    metadata = (folder / "metadata.json").read_text()
    dicted = json.loads(metadata)
    _depends = dicted.get("depends", {})
    packs = searcher.get_installed()
    for _package, data in packs.items():
        for __package, _version in data.get("depends", {}).items():
            print(__package, _package, package)
            if __package.title().replace(" ", "") == package and not force:
                logging.error(f"Package {_package} relies on package {package}. Pass --force to force removal despite this.")
                return

    log.info(f"Removed package {folder.name}")
    shutil.rmtree(folder)
    
    if not keep_depends:
        for lib, version in _depends.items():
            fold = searcher.search_package(lib, O)
            if fold:
                shutil.rmtree(fold)
                log.info(f"Removed dependency of {fold}")

manager.process_commands()