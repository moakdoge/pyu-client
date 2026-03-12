import argparse
from pathlib import Path
from typing import Any


class BaseAnnotation:
    BASE_TYPE = int
    def __init__(self, description: str = "") -> None:
        self.description = description
        self._annotation = Any
    @property
    def annotation(self):
        return self._annotation
    def __str__(self) -> str:
        raise NotImplementedError()
    def __call__(self, value) -> Any:
        raise NotImplementedError()
    @property
    def __name__(self):
        return str(self.__class__.__name__)
    
class RangeAnnotation(BaseAnnotation):
    def __init__(self, start: float, end: float,  description: str = "") -> None:
        self._start = start
        self._end = end
        return super().__init__(description=description)
    
    def __str__(self) -> str:
        return f"Accepted values: {self._start:.3f} - {self._end:.3f}"

    def __call__(self, value):
        value = float(value)

        if self._start <= value <= self._end:
            return value

        raise argparse.ArgumentTypeError(
            f"value must be between {self._start} and {self._end}"
        )
    
class NOTAnnotation(BaseAnnotation):
    def __init__(self, description: str = "", banned_values: str | list[str] = []) -> None:
        self.__banned = banned_values
        super().__init__(description)
    def __str__(self) -> str:
        return f"BANNED: ({",".join(self.__banned)})"
    def __call__(self, value) -> Any:
        if value in self.__banned:
            raise argparse.ArgumentTypeError(f"Value is banned: {value}")
        return value
    
class ExistPath:
    __name__ = "path"

    def __new__(cls, value):
        p = Path(value).expanduser()

        if not p.exists():
            raise argparse.ArgumentTypeError("Path must exist")

        return p