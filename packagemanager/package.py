import io
from pathlib import Path
import tempfile
import time
import zipfile

from .version import PackageVersion
from . import package_data
from .package_data import PackageMetadata
from . import urlfinder
import requests, shutil

class Package:
    def __init__(self, package: str, version: PackageVersion | str | None = None) -> None:
        self._package = package
        raw = requests.get(urlfinder.get_url() + f"/packages/{package}")
        if version is None:
            version = PackageVersion.from_str(raw.json()["version"])
        raw = requests.get(urlfinder.get_url() + f"/packages/{package}/{version}").json()
        if isinstance(version, str):
            version = PackageVersion.from_str(version)

        n: list[Package] = []
        for package, _version in raw.get("depends", {}).items():
            n.append(Package(package=package, version=_version))

        meta = PackageMetadata(
            name=package,
            version=version,
            author=raw.get("author", "N/A"),
            description=raw.get("description", "N/A"),
            depends=n,
            versions=[PackageVersion.from_str(v) for v in raw["versions"]],
            path=Path()
        )
        self._metadata = meta

        #self._version = version if not isinstance(version, PackageVersion) else PackageVersion.from_str(version)
    
    def download(self) -> bytes:
        '''Downloads a package and returns the bytes of the content downloaded.'''
        x=requests.get(f"{self.url}/download")
        if x.ok:
            return x.content
        else:
            raise NotImplementedError("idk..")
    
    def install(self, install_folder: Path | str) -> Path:
        if isinstance(install_folder, str):
            install_folder = Path(install_folder)

        by = self.download()
        self._metadata.path = install_folder / self.name
        b  = io.BytesIO(by)

        with tempfile.TemporaryDirectory() as z:
            with zipfile.ZipFile(b, "r") as zip:
                zip.extractall(z)
            zipped=Path(z) / (str(self.version) + ".zip")
            output = Path(z) / self.name
            with zipfile.ZipFile(zipped, "r") as f:
                f.extractall(output)
            shutil.move(output, install_folder)
        return self.path
    
    def update(self):
        new = self.newest
        if new > self.version:
            self.__init__(self._package, new)
            self.install(self.path)
        

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