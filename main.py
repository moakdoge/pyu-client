import argparse, requests, tempfile, zipfile, shutil, os, time,sys
import io
import json
from pathlib import Path
from argplus import commands
from loggingplus import *
from packagemanager import packages, searcher
from inputplus import inp
import readline


#handle arguments
manager = commands.CommandManager()
#global shit
site_packages = Path(next(x for x in sys.path if "packages" in x))




@manager.command("install")
def install(package: str, local: bool = False):
    '''Installs a package.'''
    with console.status(status=f"Installing {package}...", spinner="dots"):
        result = Path(__file__).parent if local else site_packages
        located = searcher.search_package(package, result)
        if located:
            debug.error(f"Package {package} is already installed!")
            return
        try:
            packages.download_package(package, result=result)
        except Exception as e:
            debug.error(f"{e}")
            return

        debug.info(f"Downloaded {package} successfully!")
        pass

@manager.command("debug", "logging")
def test_log():
    debug.info("This is an example of info text!")
    debug.warning("This is an example of warning text!")
    debug.error("This is an example of logging error!")

@manager.command("update")
def update(package: str, local: bool = False):
    with console.status(status=f"Updating package {package}..", spinner="dots") as con:
        result = Path(__file__).parent if local else site_packages
        con.update(status=f"Updating package {package}")
        try:
            packages.remove_package(package)
            packages.download_package(package, result=result)
        except Exception as e:
            debug.error(f"{e}")
            return

    debug.info(f"Updated {package} successfully!")


@manager.command("list")
def list_packages():
    packs = searcher.get_installed()
    lines = [f"Total packages installed: {len(packs)}", "--------------------"]
    for package, data in packs.items():
        lines.append(f"{package} - {data["author"]}")
    debug.info("\n".join(lines))

@manager.command("package", "bump")
def package_bump():
    '''Ups the version of the current package up by one. For example, 1.2.3 -> 1.2.4'''
    p = Path(os.getcwd())
    if not (p / "metadata.json").exists():
        debug.error(f"Please make sure this is a package before calling --update!")
        return
    j = json.loads((p / "metadata.json").read_text())
    part1, part2, part3 = j["version"].split(".")
    old = j["version"]
    part1 = int(part1)
    part2 = int(part2)
    part3 = int(part3)
    
    part3 += 1
    if part3 >= 10:
        part3 = 0
        part2 += 1
        if part2 >= 10:
            part1 += 1
        
    debug.info(f"Version: {old} -> {part1}.{part2}.{part3}")
    j["version"] = f"{part1}.{part2}.{part3}"
    with open((p / "metadata.json"), "w") as f:
        f.write(json.dumps(j, indent=1))
    return

@manager.command("package", "init")
def package_init():
    '''Creates a brand new package in the current directory.'''
    p = Path(os.getcwd())
    if not (p / "__init__.py").exists():
        debug.error("Please make sure you run this command inside a python module!")
        return
    if (p / "metadata.json").exists():
        cont = inp.ask("Are you sure you would like to overwrite this project? All settings will be lost!", preferred=False)
        if not cont:
            return
    
    
    auto_name = p.name.lower().replace(" ", "")
    real_name = input(f"[{auto_name}] Choose a name: ")
    if real_name.strip(" ").strip("\t").strip("\n") == "":
        real_name = auto_name
    ver = ""
    while True:
        ver = input("[1.0.0] Version: ")
        if ver == "":
            ver = "1.0.0"
        if inp.validate_version(ver):
            break
        print("Invalid version! Versions MUST be in this format: major.minor.patch")
    
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
    debug.info("Successfully created metadata.json")

@manager.command("package", "publish")
def upload_package():
    '''Uploads a package over to the server.'''
    p = Path(os.getcwd())
    if not (p / "metadata.json").exists():
        debug.error("This directory is not a valid package! Run pyu init to make it one.")
    
    name = json.loads((p / "metadata.json").read_text()).get("name")
    with console.status(status=f"Publishing {name}..."):
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
            debug.info("Successfully published package!")
        elif send.status_code == 409:
            debug.error(f"Failed to publish package! {send.json()["detail"]}")
        else:
            debug.error(f"Failed to publish package! (Error {send.status_code}, '{send.json()["detail"]}')")

@manager.command("clean")
def clean(confirm: bool = False):
    '''Wipes all installed packages.'''
    if not confirm:
        debug.warning("clean will wipe every single package installed. If this is what you want, rerun this command passing --confirm")
        return
    pack = searcher.get_installed()
    for package, data in pack.items():
        packages.remove_package(package)
        debug.info(f"Removed package {package}")

@manager.command("uninstall")
def uninstall(package: str, local: bool = False,force: bool = False, keep_depends: bool = False):
    '''Uninstalls a package'''
    debug.info('Searching for package...')
    O = (Path(os.getcwd()) if local else None)
    folder = searcher.search_package(package, O)
    if not folder:
        debug.error(f"Could not find package {package}!")
        return
    metadata = (folder / "metadata.json").read_text()
    dicted = json.loads(metadata)
    _depends = dicted.get("depends", {})
    packs = searcher.get_installed()
    for _package, data in packs.items():
        for __package, _version in data.get("depends", {}).items():
            if __package == package and not force:
                debug.error(f"Package {_package} relies on package {package}. Pass --force to force removal despite this.")
                return

    debug.info(f"Removed package {folder.name}")
    shutil.rmtree(folder)
    
    if not keep_depends:
        for lib, version in _depends.items():
            fold = searcher.search_package(lib, O)
            if fold:
                shutil.rmtree(fold)
                debug.info(f"Removed dependency of {fold}")

if __name__ == "__main__":
    manager.process_commands()