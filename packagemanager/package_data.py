from dataclasses import dataclass
from pathlib import Path
from .version import PackageVersion


@dataclass
class PackageMetadata:
    name: str
    version: PackageVersion
    author: str
    description: str
    depends: list # type: ignore
    versions: list[PackageVersion]
    path: Path
