#!/usr/bin/env python3
import argparse, requests, tempfile, zipfile, shutil, os, time,sys
import io
import json
from pathlib import Path
from argplus import commands, ctx
from typing import Annotated
from loggingplus import *
from inputplus import inp
from packagemanager.package import Package


#handle arguments
manager = commands.CommandManager("pyu")
manager.add_global("local", default=False, action="store_true")

#global shit
package_command = manager.group("package")

@manager.before_command()
def before(ctx: ctx.CommandContext):
    manager.globals.install = manager.cwd if manager.globals.local else None

@manager.exception(Exception)
def on(ctx: ctx.CommandContext, exp: Exception):
    debug.error(f"{type(exp).__name__}: {exp}")
    return False

@manager.register("install")
def install(package: str):
    '''Installs a package.'''
    
    with console.status(status=f"Installing {package}...", spinner="dots"):
        pack = Package(package=package, root=manager.globals.install)
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
    
@manager.register("update")
def update(package: str, pip: bool = False):
    global p
    '''Updates a specific package.'''
    with console.status(status=f"Updating package {package}..", spinner="dots") as con:
        con.update(status=f"Updating package {package}")
        pack = Package(package=package, root=manager.globals.install)
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
def info(package: str):
    #attempt to find package
    pack=Package(package, root=manager.globals.install)
    if not pack.exists:
        debug.error("Package not found!")
        return
    versions = [str(v) for v in pack.versions]
    versions[0] += " (latest)"
    debug.info(f'''Info about {pack.name} (@{pack.author}):\n------------------------------------------\n"{pack.description}"\n\nVersions\n{"\n".join(["\t- "+str(_) for _ in pack.versions])}
    \nMD5 hash: {pack.hash}''')

@manager.register("list")
def list_packages():
    packs = Package.find_all()
    lines = [f"Total packages installed: {len(packs)}", "--------------------"]
    for package in packs:
        if isinstance(package, Package):
            lines.append(f"{package.name} - @{package.author}")
    debug.info("\n".join(lines))

@package_command.register("bump")
def package_bump():
    '''Ups the version of the current package up by one. For example, 1.2.3 -> 1.2.4'''
    
    pack = Package.from_folder(manager.cwd)
    if not pack:
        debug.error(f"Please make sure this is a package!")
        return
    
    old = pack.version
    new = pack.version.bump()
        
    debug.info(f"Version: {old} -> {new}")
    pack._metadata.version = new
    pack.save()
    return

@package_command.register("init")
def package_init():
    '''Creates a brand new package in the current directory.'''
    if not ( manager.cwd / "__init__.py").exists():
        debug.error("Please make sure you run this command inside a python module!")
        return
    if (manager.cwd / "metadata.json").exists():
        cont = inp.ask("Are you sure you would like to overwrite this project? All settings will be lost!", preferred=False)
        if not cont:
            return
    
    
    auto_name = manager.cwd.name.lower().replace(" ", "")
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
    with open(manager.cwd / "metadata.json", "w") as m:
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

@package_command.register("publish")
def upload_package():
    '''Uploads a package over to the server.'''
    pack = Package.from_folder(manager.cwd)
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

@package_command.register("bp", aliases=["release", "bump-publish"])
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
def uninstall(package: str,force: bool = False, keep_depends: bool = False):
    '''Uninstalls a package'''
    debug.info('Searching for package...')
    pack = Package.find(package, manager.globals.install)
    if not pack:
        debug.error(f"Could not find package {package}!")
        return
    pack.remove()
    debug.info(f"Removed package {pack.name}")

    
@manager.register("test", "command", private=True)
def test_command(package: Annotated[str, "Package"]):
    print(manager.cwd, manager.globals.install)
    inst=(manager.cwd / "tmp")
    if inst.exists():
        shutil.rmtree(inst)
    inst.mkdir(exist_ok=True)

    p=Package(package,root=inst)
    p.install(False)
    time.sleep(5)
    p.remove()

@manager.register("test", "version")
def test_version(version: str, operator: str, version2: str):
    from pyu_version import PackageVersion
    v = PackageVersion.from_str(version)
    v2 = PackageVersion.from_str(version2)
    match operator:
        case ">":
            debug.info(v>v2)
        case "<":
            debug.info(v<v2)
        case ">=":
            debug.info(v>=v2)
        case "<=":
            debug.info(v<=v2)
        case "==":
            debug.info(v==v2)
        case _:
            debug.error("Invalid operator!")


@manager.register("test", "exception")
def test_exception():
    raise ValueError("Test Exception")

@manager.register("test", "logging")
def test_logging():
    from rich.table import Table
    debug.info("testing info")
    debug.warning("testing warn")
    debug.error("testing error")
    debug.info(f"quotation 'testing quotes'")
    debug.info(f"1.0, 1")
    debug.info(f'hey this is a `code block`')
    debug.info("https://www.google.com")
    t=Table(title="hi")
    t.add_row("test")
    debug.info(t)

if __name__ == "__main__":
    manager.process_commands()
