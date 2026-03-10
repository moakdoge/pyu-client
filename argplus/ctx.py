from dataclasses import dataclass
import argparse
from typing import Any

@dataclass()
class CommandContext:
    command: str
    args: argparse.Namespace
    func: Any
    return_code: int | None = None
    