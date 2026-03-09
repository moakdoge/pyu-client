import argparse, requests, tempfile, zipfile, shutil, os, time,sys
import io
import json
from pathlib import Path
from argplus import commands
from packagemanager import packages, searcher, loggerpy
import logging
from rich.console import Console 



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
    located = searcher.search_package(package, result)
    if located:
        log.error(f"Package {package} is already installed!")
        return
    log.info(f"Installing package {package} to {result}")
    try:
        packages.download_package(package, result=result)
    except Exception as e:
        log.error(f"{e}. Your command has not been executed.")
    log.info(f"Downloaded {package} successfully!")
    pass

@manager.command("test-logging")
def test_log():
    log.info("This is an example of info text!")
    log.warning("This is an example of warning text!")
    log.error("This is an example of logging error!")

@manager.command("update")
def update(package: str, local: bool = False):
    with Console().status(status=f"Updating package {package}..", spinner="dots") as con:
        result = Path(__file__).parent if local else site_packages
        con.update(status=f"Updating package {package}")
        try:
            packages.remove_package(package)
            packages.download_package(package, result=result)
        except Exception as e:
            log.error(f"{e}")
            return

    log.info(f"Updated {package} successfully!")


@manager.command("list")
def list_packages():
    packs = searcher.get_installed()
    lines = [f"Total packages installed: {len(packs)}", "--------------------"]
    for package, data in packs.items():
        lines.append(f"{package} - {data["author"]}")
    log.info("\n".join(lines))

@manager.command("init")
def package_utils():
    p = Path(os.getcwd())
    if not (p / "__init__.py").exists():
        log.error("Please make sure you run this command inside a python module!")
        return
    
    auto_name = p.name.lower().replace(" ", "")
    real_name = input(f"[{auto_name}] Choose a name: ")
    if real_name.strip(" ").strip("\t").strip("\n") == "":
        real_name = auto_name
    ver = input("[1.0.0] Version: ")
    if ver == "":
        ver = "1.0.0"
    author = input("[N/A] Author: ")
    if author == "":
        author = "N/A"
    with open(p / "metadata.json", "w") as m:
        l = json.dumps({
            "name": real_name,
            "version": ver,
            "author": author,
            "depends": {}
        }, indent=2)
        m.write(l)
    log.info("Successfully created metadata.json")

@manager.command("upload")
def upload_package():
    p = Path(os.getcwd())
    if not (p / "metadata.json").exists():
        log.error("This directory is not a valid package! Run pyu init to make it one.")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for file in Path(p).rglob("*"):
            if file.is_file():
                z.write(file, file.relative_to(p))
    buffer.seek(0)
    send = requests.post(
    url=packages.URL + "/upload",
    files={"file": ("package.zip", buffer)}
    )
    if send.ok:
        log.info("Successfully uploaded package!")
    else:
        log.error(f"Failed to upload package! (Error {send.status_code}, '{send.json()["detail"]}')")
@manager.command("clean")
def clean(confirm: bool = False):
    if not confirm:
        log.warning("clean will wipe every single package installed. If this is what you want, rerun this command passing --confirm")
        return
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
            if __package == package and not force:
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