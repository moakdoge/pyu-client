from pathlib import Path
import sys
import time
import tempfile, zipfile, os, shutil

import requests
import packagemanager.searcher as searcher
import rich
from rich.spinner import Spinner
from rich.console import Console 
from loggingplus import *
import subprocess, sys
URL = "http://192.168.0.24:5000"
def get_package(package: str, depends: bool = False) -> bytes:
    o=requests.get(f"{URL}/packages/{package}/download{"?depends=1" if depends else "?depends=0"}")
    o.raise_for_status()
    return o.content

def search_package(package: str):
    o = requests.get(f"{URL}/packages/{package}/cache")
    o.raise_for_status
    return o.json()

def install_pip_package(req: Path, local: Path | None = None) -> list[subprocess.Popen]:
    procs = []

    with open(req) as f:
        for line in f:
            pkg = line.strip()
            if not pkg or pkg.startswith("#"):
                continue

            if local is not None:
                target = (local / pkg).resolve()
                target.mkdir(parents=True, exist_ok=True)

            args = [
                sys.executable,
                "-m",
                "pip",
                "install",
                pkg,
            ]
            if local is not None:
                args.append("--target")
                args.append(str(target.absolute().resolve()))


            procs.append(
                subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
            )

    return procs

site_packages = Path(next(x for x in sys.path if "packages" in x))
def download_package(package: str, result: Path, version: str = ""):
    with tempfile.TemporaryDirectory() as z:
        tmp = Path(z)
        with open(tmp / "output.zip", "wb") as f:
            if version != "":
                f.write(get_package(package, True))
            else:
        
                f.write(get_package(package, True))

        with zipfile.ZipFile(tmp / "output.zip", "r") as zipped:
            zipped.extractall(tmp)

        folders: list[Path] = []
        os.remove(tmp / "output.zip")
        for zipf in tmp.glob("*.zip"):
            d = (tmp / f"{zipf.name.rstrip(".zip").split("-")[0]}")
            d.mkdir(exist_ok=True)
            with zipfile.ZipFile(zipf, "r") as _tmp:
                _tmp.extractall(d)

            r=(d / "requirements.txt")
            if r.exists():
                _=result
                if result == site_packages:
                    _ = None
                k=install_pip_package(r, local=_)
                for proc in k:
                    proc.wait()

            os.remove(zipf)
            folders.append(d)
        for folder in folders:
            result_path = (result.absolute() / folder.name)
            if not result_path.exists():
                shutil.copytree(folder.absolute(), result.absolute() / folder.name)
                continue
            else:
                pass
                # print(f"Skipped {folder.name} - Not valid (file exists)")

        
def remove_package(package: str):
    pck = searcher.search_package(package)
    if not pck:
        raise FileNotFoundError(f"Package {package} not found!")
    shutil.rmtree(pck)