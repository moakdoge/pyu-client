from dataclasses import dataclass


@dataclass(frozen=True)
class PackageVersion:
    major: int
    minor: int
    patch: int
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __le__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)
    
    def __gt__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)
    
    def __ge__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)
    
    def __eq__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))
    
    @classmethod
    def from_str(cls, st: str):
        parts = st.split(".")
        
        parts = [int(p.replace("=", "").replace(">", "")) for p in parts]
        return cls(*parts)
    
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
        return PackageVersion(major=part1, minor=part2, patch=part3)