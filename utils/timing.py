import logging
import time

logger = logging.getLogger("hx_test")


class Timer:
    """Context manager that logs the duration of a timed step."""

    def __init__(self, label: str):
        self.label = label
        self.elapsed: float = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        logger.info("[TIMER] %s — started", self.label)
        return self

    def __exit__(self, *exc):
        self.elapsed = time.perf_counter() - self.start
        logger.info("[TIMER] %s — finished in %.2fs", self.label, self.elapsed)
        return False
