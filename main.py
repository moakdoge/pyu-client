#!/usr/bin/env python3
import argparse, requests, tempfile, zipfile, shutil, os, time,sys
import io
import json
from pathlib import Path
from argplus import commands, ctx
from typing import Annotated
from loggingplus import *
from packagemanager import packages, searcher, version
from inputplus import inp
from packagemanager.package import Package


#handle arguments
manager = commands.CommandManager("pyu")
p = Path(os.getcwd())
#global shit

deb = manager.group("package")


@manager.register("install")
def install(package: str, local: bool = False):
    '''Installs a package.'''
    
    with console.status(status=f"Installing {package}...", spinner="dots"):
        result = p if local else None
        pack = Package(package=package, root=result)
        if pack.exists:
            debug.error(f"Package {package} is already installed!")
            return
        try:
            pack.install(True)
        except Exception as e:
            debug.error(f"{e}")
            return

        debug.info(f"Downloaded {package} successfully!")
        pass
    

@deb.register("logging")
def test_log():
    debug.info("This is an example of info text!")
    debug.warning("This is an example of warning text!")
    debug.error("This is an example of logging error!")

@manager.register("update")
def update(package: str, local: bool = False, pip: bool = False):
    global p
    '''Updates a specific package.'''
    with console.status(status=f"Updating package {package}..", spinner="dots") as con:
        result = p if local else None
        con.update(status=f"Updating package {package}")
        pack = Package(package=package, root=result)
        if not pack.exists:
            debug.error(f"Package {package} is not installed!")
            return
        
        current_ver = pack.version
        new_ver = pack.newest
        try:
            if current_ver >= new_ver:
                debug.info(f"No updates detected.")
                return
            pack.remove()
            pack.install(False)
            debug.info(f"{package}: {current_ver} -> {new_ver}")
        except Exception as e:
            debug.error(f"{e}")
            return


@manager.register("info")
def info(package: str, local: bool = False):
    #attempt to find package
    result = p if local else None
    pack=Package(package, root=result)
    if not pack.exists:
        debug.error("Package not found!")
        return
    versions = [str(v) for v in pack.versions]
    versions[0] += " (latest)"
    debug.info(f'''Info about {pack.name} (@{pack.author}):\n------------------------------------------\n"{pack.description}"\n\nVersions\n{"\n".join(["\t- "+str(_) for _ in pack.versions])}
    \nMD5 hash: {pack.hash}''')

@manager.register("list")
def list_packages():
    packs = searcher.get_installed()
    lines = [f"Total packages installed: {len(packs)}", "--------------------"]
    for package, data in packs.items():
        lines.append(f"{package} - @{data["author"]}")
    debug.info("\n".join(lines))

@manager.register("package", "bump")
def package_bump():
    '''Ups the version of the current package up by one. For example, 1.2.3 -> 1.2.4'''
    
    pack = Package.from_folder(Path(os.getcwd()))
    if not pack:
        debug.error(f"Please make sure this is a package before calling --update!")
        return
    
    part1, part2, part3 = (pack.version.major, pack.version.minor, pack.version.patch)
    old = pack.version
    part1 = int(part1)
    part2 = int(part2)
    part3 = int(part3)
    
    part3 += 1
    if part3 >= 100:
        part3 = 0
        part2 += 1
        if part2 >= 100:
            part2 = 0
            part1 += 1
        
    debug.info(f"Version: {old} -> {part1}.{part2}.{part3}")
    pack._metadata.version = version.PackageVersion(part1, part2, part3)
    pack.save()
    return

@manager.register("package", "init")
def package_init():
    '''Creates a brand new package in the current directory.'''
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
    descr = input("Description:")
    with open(p / "metadata.json", "w") as m:
        l = json.dumps({
            "name": real_name,
            "version": ver,
            "author": author,
            "depends": {},
            "description": descr,
            "language": "python"
        }, indent=2)
        m.write(l)
    
    debug.info("Successfully created metadata.json")

@manager.register("package", "publish")
def upload_package():
    '''Uploads a package over to the server.'''
    pack = Package.from_folder(Path(os.getcwd()))
    if pack is None:
        debug.error("Not a valid package! run `pyu init` to make it one.")
        return
    name = pack.name
    with console.status(status=f"Publishing {name}..."):
        send = pack.upload()
        if send.ok:
            debug.info("Successfully published package!")
        elif send.status_code == 409:
            debug.error(f"Failed to publish package! {send.json()["detail"]}")
        else:
            debug.error(f"Failed to publish package! (Error {send.status_code}, '{send.json()["detail"]}')")

@manager.register("package", "bp", aliases=["release", "bump-publish"])
def bp():
    '''Will automatically bump the package and publish it.'''
    manager.run("package", "bump")
    manager.run("package", "publish")

@manager.register("clean")
def clean(confirm: bool = False):
    '''Wipes all installed packages.'''
    if not confirm:
        debug.warning("clean will wipe every single package installed. If this is what you want, rerun this command passing --confirm")
        return
    packs = Package.find_all()
    for package in packs:
        if isinstance(package, Package):
            package.remove()
            debug.info(f"Removed package {package.name}")

@manager.register("uninstall")
def uninstall(package: str, local: bool = False,force: bool = False, keep_depends: bool = False):
    '''Uninstalls a package'''
    debug.info('Searching for package...')
    O = (p if local else None)
    pack = Package.find(package, O)
    if not pack:
        debug.error(f"Could not find package {package}!")
        return
    pack.remove()
    debug.info(f"Removed package {pack.name}")

    
@manager.register("test", "command")
def test_command(package: str):
    inst=(Path(os.getcwd()) / "tmp")
    if inst.exists():
        shutil.rmtree(inst)
    inst.mkdir(exist_ok=True)

    p=Package(package,root=inst)
    p.install(False)
    time.sleep(5)
    p.remove()

if __name__ == "__main__":
    manager.process_commands()