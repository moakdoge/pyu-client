import argparse, requests

URL = "http://127.0.0.1:5000"

parser = argparse.ArgumentParser()
parser.add_argument("--package", "-p", required=True)
args = parser.parse_args()

package = args.package

def get_package(package: str, depends: bool = False) -> bytes:
    o=requests.get(f"{URL}/packages/{package}/download{"?depends=1" if depends else "?depends=0"}")
    o.raise_for_status()
    return o.content

with open("output.zip", "wb") as f:
    f.write(get_package(package, True))