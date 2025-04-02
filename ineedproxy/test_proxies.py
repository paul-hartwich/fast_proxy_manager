from typing import Tuple, List, Union, Dict
from random import shuffle
import asyncio

from .utils import ProxyDict
from .logger import logger

import aiohttp


async def _is_proxy_valid(proxy: ProxyDict, session: aiohttp.ClientSession,
                          supported_protocols: Tuple[str] = ('http', 'https')) -> Union[ProxyDict, None]:
    """Proxy dictionary must contain 'url' or 'proxy' key or 'ip', 'port', 'protocol' keys"""
    url = proxy["url"]
    protocol = url.protocol

    if protocol not in supported_protocols:
        return None

    try:
        async with session.get("https://httpbin.org/ip", proxy=url, allow_redirects=True, timeout=20) as response:
            if response.status == 200:
                logger.debug("Valid: %s", url)
                return proxy
            return None
    except (asyncio.TimeoutError, aiohttp.ClientError, ConnectionResetError):
        return None


async def get_valid_proxies(proxies: List[ProxyDict], max_working_proxies: Union[int, False] = False,
                            simultaneous_proxy_requests=int) -> List[ProxyDict]:
    """Dict must contain 'url' key or preferably 'ip' and 'port' keys."""
    valid_proxies = []
    if not all(isinstance(proxy, dict) for proxy in proxies):
        raise ValueError("All items in the proxies list must be dictionaries")
    shuffle(proxies)
    semaphore = asyncio.Semaphore(simultaneous_proxy_requests)

    async with aiohttp.ClientSession() as session:
        async def limited_is_proxy_valid(proxy: Dict) -> Union[ProxyDict, None]:
            async with semaphore:
                if max_working_proxies and len(valid_proxies) >= max_working_proxies:
                    return None
                result = await _is_proxy_valid(proxy, session)
                if result:
                    valid_proxies.append(result)
                return result

        tasks = [limited_is_proxy_valid(proxy) for proxy in proxies]
        await asyncio.gather(*tasks)

    return valid_proxies[:max_working_proxies] if max_working_proxies else valid_proxies
