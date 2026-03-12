from dataclasses import dataclass
from .version import PackageVersion


@dataclass
class PackageMetadata:
    name: str
    version: PackageVersion
    author: str
    description: str
    depends: dict # type: ignore
    versions: list[PackageVersion]
