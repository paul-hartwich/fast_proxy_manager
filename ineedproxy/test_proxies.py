from typing import Tuple, List, Union, Dict, Optional
from random import shuffle
import asyncio

from .utils import ProxyDict
from .logger import logger

import aiohttp


async def _is_proxy_valid(
        proxy: ProxyDict,
        session: aiohttp.ClientSession,
        test_url: str = "https://httpbin.org/ip",
        timeout: int = 20,
        supported_protocols: Tuple[str, ...] = ('http', 'https')
) -> Optional[ProxyDict]:
    """
    Test if a proxy is valid by making a request through it.

    Args:
        proxy: Proxy dictionary containing URL information
        session: aiohttp client session to use
        test_url: URL to test the proxy against
        timeout: Timeout in seconds
        supported_protocols: Tuple of supported proxy protocols

    Returns:
        The proxy dict if valid, None otherwise
    """
    url = proxy.get("url")
    if not url:
        return None

    protocol = getattr(url, 'protocol', None)
    if not protocol:
        try:
            protocol = str(url).split('://')[0]
        except (IndexError, AttributeError):
            return None

    if protocol not in supported_protocols:
        return None

    try:
        proxy_str = str(url)
        async with session.get(
                test_url,
                proxy=proxy_str,
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            if response.status == 200:
                try:
                    json_data = await response.json()
                    if 'origin' in json_data:
                        logger.debug(f"Valid: {url}")
                        return proxy
                except:
                    pass
            return None

    except Exception:
        return None


async def get_valid_proxies(
        proxies: List[ProxyDict],
        max_working_proxies: Union[int, bool] = False,
        simultaneous_proxy_requests: int = 50,
        test_url: str = "https://httpbin.org/ip",
        timeout: int = 20
) -> List[ProxyDict]:
    """
    Test multiple proxies concurrently and return those that are valid.

    Args:
        proxies: List of proxy dictionaries to test
        max_working_proxies: Maximum number of working proxies to return, or False for all
        simultaneous_proxy_requests: Maximum number of concurrent proxy tests
        test_url: URL to test proxies against
        timeout: Timeout for each proxy test in seconds

    Returns:
        List of valid proxy dictionaries

    Raises:
        ValueError: If proxies list contains non-dictionary items
    """
    valid_proxies = []

    if not proxies:
        return valid_proxies

    if not all(isinstance(proxy, dict) for proxy in proxies):
        raise ValueError("All items in the proxies list must be dictionaries")

    proxies_copy = proxies.copy()
    shuffle(proxies_copy)

    semaphore = asyncio.Semaphore(simultaneous_proxy_requests)
    lock = asyncio.Lock()

    async with aiohttp.ClientSession() as session:
        async def limited_is_proxy_valid(proxy: Dict) -> Optional[ProxyDict]:
            async with semaphore:
                async with lock:
                    if isinstance(max_working_proxies, int) and len(valid_proxies) >= max_working_proxies:
                        return None

                result = await _is_proxy_valid(proxy, session, test_url, timeout)

                if result:
                    async with lock:
                        valid_proxies.append(result)
                        if isinstance(max_working_proxies, int) and len(valid_proxies) >= max_working_proxies:
                            for task in pending:
                                if not task.done():
                                    task.cancel()
                return result

        tasks = [asyncio.create_task(limited_is_proxy_valid(proxy)) for proxy in proxies_copy]
        pending = tasks.copy()

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

        if isinstance(max_working_proxies, int):
            return valid_proxies[:max_working_proxies]
        return valid_proxies
