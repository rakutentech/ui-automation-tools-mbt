from functools import wraps
from time import time


def timeit(func):
    """
    A stop watch decorator.
    """
    @wraps(func)
    def _time_it(*args, **kwargs):
        start = time()
        return func(*args, **kwargs), time() - start
    return _time_it
