import timeit
from icecream import ic
from functools import wraps


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = timeit.default_timer()
        result = func(*args, **kwargs)
        end = timeit.default_timer()
        interval = end - start
        ic(f"Elapsed time: {interval:.3f} seconds")
        return result

    return wrapper


def async_timer(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = timeit.default_timer()
        result = await func(*args, **kwargs)
        end = timeit.default_timer()
        interval = end - start
        ic(f"Elapsed time: {interval:.3f} seconds")
        return result

    return wrapper


class Timer:
    def __enter__(self):
        self.start = timeit.default_timer()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = timeit.default_timer()
        self.interval = self.end - self.start
        ic(f"Elapsed time: {self.interval:.3f} seconds")


class AsyncTimer:
    async def __aenter__(self):
        self.start = timeit.default_timer()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end = timeit.default_timer()
        self.interval = self.end - self.start
        ic(f"Elapsed time: {self.interval:.3f} seconds")
