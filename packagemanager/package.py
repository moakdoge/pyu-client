import io
import json
from pathlib import Path
import tempfile
import time
import zipfile, hashlib

from .version import PackageVersion
from . import package_data
from .package_data import PackageMetadata
from . import urlfinder
import requests, shutil, sys
site_packages = Path(next(x for x in sys.path if "packages" in x))
class Package:
    def __init__(self, package: str, version: PackageVersion | str | None = None, root: Path | None = site_packages) -> None:
        self._package = package
        if not root:
            root = site_packages
        raw = requests.get(urlfinder.get_url() + f"/packages/{package}")
        self._hash = raw.json()["hash"]
        if version is None:
            version = PackageVersion.from_str(raw.json()["version"])
        raw = requests.get(urlfinder.get_url() + f"/packages/{package}/{version}").json()
        if isinstance(version, str):
            version = PackageVersion.from_str(version)

        n: list[Package] = []
        for _pk, _version in raw.get("depends", {}).items():
            n.append(Package(package=_pk, version=_version, root=root))
        _versions=[PackageVersion.from_str(v) for v in raw.get("versions", [])]
        _versions.sort(reverse=True)
        meta = PackageMetadata(
            name=package,
            version=version,
            author=raw.get("author", "N/A"),
            description=raw.get("description", "N/A"),
            depends=n,
            versions=_versions,
            path=(root / package)
        )
        self._metadata = meta

    @classmethod
    def from_folder(cls, folder: Path):
        if not folder.exists():
            raise FileNotFoundError
        if (folder / "metadata.json").exists():
            loaded = json.loads((folder / "metadata.json").read_text())
            return cls(loaded["name"], root=folder.parent)
        #self._version = version if not isinstance(version, PackageVersion) else PackageVersion.from_str(version)
    
    @staticmethod
    def find_all(folder: Path = site_packages) -> list:
        _: list[Package] = []
        for f in folder.glob("*"):
            if f.is_file():
                continue
            try:
                p = Package.from_folder(f)
                if p:
                    _.append(p)
            except Exception:
                continue
        return _
    def download(self) -> bytes:
        '''Downloads a package and returns the bytes of the content downloaded.'''
        x=requests.get(f"{self.url}/download?depends=0")
        if x.ok:
            return x.content
        else:
            raise NotImplementedError("idk..")
    
    def _install_dependencies(self):
        for depend in self._metadata.depends:
            if isinstance(depend, Package):
                depend.install(False)

    def install(self, dependencies:bool=True) -> Path:
        by = self.download()
#        if hashlib.md5(by).hexdigest() != self.hash:
#            raise Exception(f"File failed checksum check!")
        b  = io.BytesIO(by)
        if dependencies:
            self._install_dependencies()
        with tempfile.TemporaryDirectory() as z:
            
            with zipfile.ZipFile(b, "r") as zip:
                zip.extractall(Path(z) / self._package)
            shutil.move(Path(z) / self._package, self.path)
        return self.path

    def remove(self):
        if self.path.exists():
            shutil.rmtree(self.path)

    @property
    def url(self):
        return f"{urlfinder.get_url()}/packages/{self._package}/{self.version}"
    
    @property
    def name(self):
        return self._metadata.name

    @property
    def author(self):
        return self._metadata.author
    
    @property
    def description(self):
        return self._metadata.description
    
    @property
    def depends(self):
        return self._metadata.depends
    
    @property
    def versions(self):
        return self._metadata.versions
    
    @property
    def version(self):
        return self._metadata.version
    
    @property
    def path(self):
        return self._metadata.path
    
    @property
    def newest(self) -> PackageVersion:
       x=requests.get(f"{urlfinder.get_url()}/packages/{self._package}")
       x.raise_for_status()
       return PackageVersion.from_str(x.json()["version"])
    
    @property
    def exists(self):
        return self.path.exists()
    
    @property
    def hash(self):
        return self._hash
    
    def save(self):
        with open(self.path / "metadata.json", "w") as f:
            data = self._metadata.dump()
            f.write(json.dumps(data, indent=2))
    
    def upload(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            for file in Path(self.path).rglob("*"):
                if file.is_file():
                    z.write(file, file.relative_to(self.path))
        buffer.seek(0)
        send = requests.post(
            url=urlfinder.get_url() + "/upload",
            files={"file": ("package.zip", buffer)}
        )
        return send