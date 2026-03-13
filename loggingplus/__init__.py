import logging
import rich.console as _cls
from io import StringIO
import datetime
import re
from rich.logging import RichHandler

from rich.syntax import Syntax
from rich.panel import Panel
class CleanFormatter(logging.Formatter):
    
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
    INLINE_LINK_PATTERN = re.compile(r'\b((?:https?|ftp)://[^\s<>()]+|www\.[^\s<>()]+)')
    def _style_links(self, message: str) -> str:
        return re.sub(self.INLINE_LINK_PATTERN, r"[link=\g<1>]\g<1>[/link]", message)
    
    def _style_inline_code(self, message: str) -> str:
        parts = []

        cursor = 0
        for match in self.INLINE_CODE_PATTERN.finditer(message):
            start, end = match.span()
            parts.append(message[cursor:start])

            parts.append(f"[blue bold]{match.group(1)}[/blue bold]")

            cursor = end
        parts.append(message[cursor:])
        return "".join(parts)

    def _format(self, record: logging.LogRecord) -> str:
        
        name = f"[{record.levelname}]"
        match record.levelno:
            case self.DEBUG:
                name = "[white]" + name + "[/white]"
            case self.INFO:
                name = "[gray]" + name + "[/gray]"
            case self.WARN:
                name = "[yellow]" + name + "[/yellow]"
            case self.ERROR:
                name = "[red]" + name + "[/red]"
            case self.CRITICAL:
                name = "[bold red]" + name + "[/bold red]"
            case _:
                pass

            
        
        t=datetime.datetime.fromtimestamp(record.created)
        timestamp = f"[blue]{t.hour}:{t.minute}:{t.second}.{record.msecs:.0f} [/blue]"
        message = self._style_inline_code(record.getMessage())
        message = self._style_links(message)
        return f"{timestamp} {name}: {message}"

    def format(self, record: logging.LogRecord) -> str:
        buffer = StringIO()
        _cls.Console(file=buffer, force_terminal=True).print(self._format(record), markup=True, end="")
        return buffer.getvalue()
    


handler = logging.StreamHandler()
handler.setFormatter(CleanFormatter())


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler()]
)

debug = logging.getLogger(__name__)
debug.addHandler(handler)
debug.propagate = False
console = _cls.Console()