import logging
import os
import sys
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from queue import Queue

import yaml


def load_yaml(filename: str | Path):
    with open(filename) as file:
        return yaml.safe_load(file)


def rate_limit(interval: float):

    def decorator(f):

        last_called: float | None = None

        @wraps(f)
        def wrapper(*args, **kwargs):
            nonlocal last_called
            now = time.perf_counter()
            if last_called and now - last_called < interval:
                return
            last_called = now
            return f(*args, **kwargs)

        return wrapper

    return decorator


@contextmanager
def ignore_stderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        old_stderr = os.dup(2)
        try:
            sys.stderr.flush()
            os.dup2(devnull, 2)
            try:
                yield
            finally:
                os.dup2(old_stderr, 2)
        finally:
            os.close(old_stderr)
    finally:
        os.close(devnull)


def queue_get_non_blocking(queue: Queue):
    return queue.get(block=False) if not queue.empty() else None


def timestamp_now():
    return time.time()


@contextmanager
def no_exceptions():
    try:
        yield
    except Exception as ex:
        # ошибку только логируем, в toast не показываем, чтобы не спамить
        logging.exception('ERROR: %s', ex)
