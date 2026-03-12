from .version import PackageVersion
from . import package_data
from .package_data import PackageMetadata
from . import urlfinder
import requests

class Package:
    def __init__(self, package: str, version: PackageVersion | str | None = None) -> None:
        self._package = package
        raw = requests.get(urlfinder.get_url() + f"/packages/{package}")
        if version is None:
            version = PackageVersion.from_str(raw.json()["version"])
        raw = requests.get(urlfinder.get_url() + f"/packages/{package}/{version}").json()
        if isinstance(version, str):
            version = PackageVersion.from_str(version)
        meta = PackageMetadata(
            name=package,
            version=version,
            author=raw.get("author", "N/A"),
            description=raw.get("description", "N/A"),
            depends=raw.get("depends", {}),
            versions=[PackageVersion.from_str(v) for v in raw["versions"]]
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