import io
from pathlib import Path
import tempfile
import time
import zipfile

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
        if version is None:
            version = PackageVersion.from_str(raw.json()["version"])
        raw = requests.get(urlfinder.get_url() + f"/packages/{package}/{version}").json()
        if isinstance(version, str):
            version = PackageVersion.from_str(version)

        n: list[Package] = []
        for _pk, _version in raw.get("depends", {}).items():
            n.append(Package(package=_pk, version=_version, root=root))

        meta = PackageMetadata(
            name=package,
            version=version,
            author=raw.get("author", "N/A"),
            description=raw.get("description", "N/A"),
            depends=n,
            versions=[PackageVersion.from_str(v) for v in raw.get("versions", [])],
            path=(root / package)
        )
        self._metadata = meta


        #self._version = version if not isinstance(version, PackageVersion) else PackageVersion.from_str(version)
    
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
                print(depend.url, depend.path, self.path)
                depend.install(False)

    def install(self, dependencies:bool=True) -> Path:
        by = self.download()
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