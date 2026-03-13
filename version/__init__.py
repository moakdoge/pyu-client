from dataclasses import dataclass
import re
_CACHED = re.compile(
    r"^(?:v)?(?:(\d+)!)?(\d+(?:[._-]\d+)*)(?:[-._]?([a-zA-Z]+)(\d+)?)?$"
)


_ALLOWED_TAGS = ["rc", "b", "a", ".dev"][::-1]

@dataclass()
class PackageVersion:
    major: int
    minor: int
    patch: int
    epoch: int = 0
    tag: str = ""
    tag_version: int = 0

    def __post_init__(self):
        _allowed = False
        if self.tag == "":
            self.tag_version = -1
            return
        
        
    def __str__(self):
        base = f"{self.major}.{self.minor}.{self.patch}"
        t=self.tag_version if self.tag_version else ""
        return base + self.tag + str(t) if self.tag else base
    
    def __lt__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple < other.tuple 
    
    def __le__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple <= other.tuple 
    
    def __gt__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple > other.tuple 
    
    def __ge__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple >= other.tuple 
    
    def __eq__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple == other.tuple 
    
    def __hash__(self) -> int:
        return hash(self.tuple)
        
    @classmethod
    def from_str(cls, st: str):
        match = _CACHED.match(st)
        if not match:
            raise ValueError("Invalid version string!")

        epoch = int(match.group(1)) if match.group(1) else 0
        nums = match.group(2).split(".")
        tag = match.group(3) or ""
        tag_version = int(match.group(4) or 0)

        major = int(nums[0])
        minor = int(nums[1]) if len(nums) > 1 else 0
        patch = int(nums[2]) if len(nums) > 2 else 0

        return cls(major, minor, patch, tag=tag, epoch=epoch, tag_version=tag_version)

        
    def bump(self):
        part1 = int(self.major)
        part2 = int(self.minor)
        part3 = int(self.patch)
        
        part3 += 1
        if part3 >= 100:
            part3 = 0
            part2 += 1
            if part2 >= 100:
                part2 = 0
                part1 += 1
        return PackageVersion(major=part1, minor=part2, patch=part3, tag=self.tag)
    
    @property
    def tuple(self):
        tag_priority = _ALLOWED_TAGS.index(self.tag) if self.tag in _ALLOWED_TAGS else -1
        return (self.epoch, self.major, self.minor, self.patch, tag_priority, self.tag_version)
    def __iter__(self):
        yield from self.tuple