from pathlib import Path
import tempfile, zipfile, os, shutil

import requests
import packagemanager.searcher as searcher

URL = "http://127.0.0.1:5000"
def get_package(package: str, depends: bool = False) -> bytes:
    o=requests.get(f"{URL}/packages/{package}/download{"?depends=1" if depends else "?depends=0"}")
    o.raise_for_status()
    return o.content

def download_package(package: str, result: Path, version: str = ""):
    with tempfile.TemporaryDirectory() as z:
        tmp = Path(z)
        with open(tmp / "output.zip", "wb") as f:
            if version != "":
                f.write(get_package(package, True))
            else:
                f.write(get_package(package, True))
        zipped = zipfile.ZipFile(tmp / "output.zip", "r")
        zipped.extractall(tmp)
        zipped.close()
        folders: list[Path] = []
        os.remove(tmp / "output.zip")
        for zipf in tmp.glob("*.zip"):
            d = (tmp / f"{zipf.name.rstrip(".zip").split("-")[0]}")
            d.mkdir(exist_ok=True)
            _tmp = zipfile.ZipFile(zipf, "r")
            _tmp.extractall(d)
            _tmp.close()
            os.remove(zipf)

            folders.append(d)
        for folder in folders:
            result_path = (result.absolute() / folder.name)
            if not result_path.exists():
                shutil.copytree(folder.absolute(), result.absolute() / folder.name)
                continue
            else:
                print(f"Skipped {folder.name} - Not valid (file exists)")

        
def remove_package(package: str):
    pck = searcher.search_package(package)
    if not pck:
        raise FileNotFoundError(f"Package {package} not found!")
    shutil.rmtree(pck)