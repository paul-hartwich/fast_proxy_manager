# -*- coding: utf-8 -*-
"""
Library module initialization.
"""

from typing import Tuple, List
from functools import partial

from .manager import Manager
from .utils import NoProxyAvailable, ProxyDict, URL
from .get import fetch_json_proxy_list, fetch_github_proxifly


class Fetch:
    @staticmethod
    async def proxifly() -> List[ProxyDict]:
        """Fetch proxies from proxifly. Very large list. It May take a long while."""
        return await fetch_github_proxifly()

    @staticmethod
    async def custom(url: str) -> List[ProxyDict]:
        """Fetch proxies from a custom url. Can be better and faster."""
        return await fetch_json_proxy_list(url)


# Version information
from . import version

# Define what will be imported with `from library import *`
__all__: Tuple[str, ...] = (
    "Manager",
    "NoProxyAvailable",
    "ProxyDict",
    "URL",
    "Fetch",
    "__version__",
    "partial",  # directly import partial from functools
)

__version__ = version.__version__


def __dir__() -> Tuple[str, ...]:
    return list(__all__) + ["__doc__"]
