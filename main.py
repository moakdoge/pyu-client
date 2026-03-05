import argparse, requests, tempfile, zipfile, shutil, os, time
from pathlib import Path
URL = "http://127.0.0.1:5000"

parser = argparse.ArgumentParser()
parser.add_argument("--package", "-p", required=True)
parser.add_argument("--local", "-l", type=bool, default=True)
args = parser.parse_args()

package = args.package

def get_package(package: str, depends: bool = False) -> bytes:
    o=requests.get(f"{URL}/packages/{package}/download{"?depends=1" if depends else "?depends=0"}")
    o.raise_for_status()
    return o.content

with tempfile.TemporaryDirectory() as z:
    tmp = Path(z)
    with open(tmp / "output.zip", "wb") as f:
        f.write(get_package(package, True))
    zipped = zipfile.ZipFile(tmp / "output.zip", "r")
    zipped.extractall(tmp)
    os.remove(tmp / "output.zip")
    for zipf in tmp.glob("*.zip"):
        d = (tmp / f"{zipf.name.rstrip(".zip").split("-")[0]}")
        d.mkdir(exist_ok=True)
        _tmp = zipfile.ZipFile(zipf, "r")
        _tmp.extractall(d)
        os.remove(zipf)
    print(tmp)
    time.sleep(500)   
    