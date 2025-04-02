# -*- coding: utf-8 -*-
"""
Library module initialization.
"""

from typing import Tuple, List

from .manager import Manager
from .utils import NoProxyAvailable, ProxyPreferences, ProxyDict, URL
from .get import fetch_json_proxy_list

# Version information
from . import version

# Define what will be imported with `from library import *`
__all__: Tuple[str, ...] = (
    "Manager",
    "NoProxyAvailable",
    "ProxyPreferences",
    "ProxyDict",
    "URL",
    "fetch_json_proxy_list",
    "__version__",
)

__version__ = version.__version__


def __dir__() -> Tuple[str, ...]:
    return list(__all__) + ["__doc__"]
