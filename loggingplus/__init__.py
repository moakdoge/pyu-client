import logging as __logging
from rich.logging import RichHandler
import rich.console as _cls
__logging.basicConfig(
    level=__logging.INFO,
    format="%(message)s",
    handlers=[RichHandler()]
)

debug = __logging.getLogger(__name__)
console = _cls.Console()