import logging
from functools import wraps

from common.toast import toast, ToastKind


def handle_error(f):

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as ex:
            this, *_ = args
            logging.exception('ERROR: %s', ex)
            toast(ex, kind=ToastKind.ERROR)

    return wrapper
