import contextlib
import logging
from dataclasses import dataclass
from pathlib import Path
from timeit import default_timer as timer

logger = logging.getLogger(__name__)


@dataclass
class DurationLogger:
    path: Path

    @contextlib.contextmanager
    def log_time(self, message: str):
        start = timer()
        yield
        total_duration = f'{message}: {timer() - start}s.'
        logger.info(total_duration)
        with self.path.open('a') as f:
            f.writelines(total_duration)
            f.write('\n')
