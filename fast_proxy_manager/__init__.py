from typing import List

from fast_proxy_manager.controller import Controller
from fast_proxy_manager.utils import NoProxyAvailable, ProxyDict, URL
from fast_proxy_manager.get import fetch_json_proxy_list, fetch_github_proxifly


class Fetch:
    @staticmethod
    async def proxifly() -> List[ProxyDict]:
        """Fetch proxies from proxifly. Very large list. It May take a long while."""
        return await fetch_github_proxifly()

    @staticmethod
    async def custom(url: str) -> List[ProxyDict]:
        """Fetch proxies from a custom url. Can be better and faster."""
        return await fetch_json_proxy_list(url)


__all__ = ['Controller', 'NoProxyAvailable', 'ProxyDict', 'URL', 'Fetch']
