import json
from pathlib import Path
import sys


site_packages = Path(next(x for x in sys.path if "packages" in x))

def folder_is_package(folder: Path):
    if folder.is_file():
        return False
    if not folder.exists():
        return False
    return (folder / "metadata.json").exists()
    

def search_package(package: str, path: Path | None = None) -> Path | None:
    _path = path
    if _path is None:
        _path = site_packages
    
    for folder in _path.glob("*"):
        if not folder_is_package(folder):
            continue
        metadata = (folder / "metadata.json").read_text()
        dicted = json.loads(metadata)
        _name = dicted["name"]
    

        if _name == package or package == folder.name:
            return folder
    return None

def get_installed(path: Path | None = None):
    _path = path
    if _path is None:
        _path = site_packages

    packages = {}
    for folder in _path.glob("*"):
        if not folder_is_package(folder):
            continue
        metadata = (folder / "metadata.json").read_text()
        dicted = json.loads(metadata)
        packages[folder.name] = dicted
    return packages