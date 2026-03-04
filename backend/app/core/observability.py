from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("cdg_support")


def log_event(event: str, **kwargs) -> None:
    payload = {"event": event, **kwargs}
    logger.info(json.dumps(payload, ensure_ascii=False))


@contextmanager
def latency_metric(metric_name: str, **tags):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        log_event("latency", metric=metric_name, elapsed_ms=elapsed_ms, **tags)
