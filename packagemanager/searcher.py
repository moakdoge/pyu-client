import json
from pathlib import Path
import sys

site_packages = Path(next(x for x in sys.path if "packages" in x))

def search_package(package: str, path: Path | None = None) -> Path | None:
    _path = path
    if _path is None:
        _path = site_packages
    
    for folder in _path.glob("*"):
        if folder.is_file():
            continue
        WATERMARK = (folder / "WATERMARK")
        if not WATERMARK.exists():
            continue

        
        metadata = (folder / "metadata.json").read_text()
        dicted = json.loads(metadata)
        _name = dicted["name"]
    

        if _name == package or package == folder.name:
            return folder
    return None