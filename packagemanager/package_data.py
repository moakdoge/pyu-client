from dataclasses import dataclass
from pathlib import Path
from version import PackageVersion


@dataclass
class PackageMetadata:
    name: str
    version: PackageVersion
    author: str
    description: str
    depends: list # type: ignore
    versions: list[PackageVersion]
    path: Path
    def dump(self) -> dict:
        n = {}
        for d in self.depends:
            n[d.name] = str(d.version)
        return {
            "name": self.name,
            "version": str(self.version),
            "author": str(self.author),
            "description": "",
            "depends": n,
            "language": "python"
        }