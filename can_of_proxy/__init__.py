from typing import List

from can_of_proxy.can import Can
from can_of_proxy.utils import NoProxyAvailable, ProxyDict, URL
from can_of_proxy.get import fetch_json_proxy_list, fetch_github_proxifly


class Fetch:
    @staticmethod
    async def proxifly() -> List[ProxyDict]:
        """Fetch proxies from proxifly. Very large list. It May take a long while."""
        return await fetch_github_proxifly()

    @staticmethod
    async def custom(url: str) -> List[ProxyDict]:
        """Fetch proxies from a custom url. Can be better and faster."""
        return await fetch_json_proxy_list(url)


__all__ = ['Can', 'NoProxyAvailable', 'ProxyDict', 'URL', 'Fetch']
