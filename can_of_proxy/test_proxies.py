import asyncio
from typing import List, Tuple, Any
import aiohttp
from icecream import ic


async def is_proxy_valid(proxy_complete_url: str) -> Tuple[bool, Any]:
    """
    Check if a proxy is valid by checking if the IP is reachable through the proxy.
    :param proxy_complete_url: example: http://ip:port
    """
    if ':' not in proxy_complete_url.split('//')[-1]:
        return False, None

    proxy_formatted = {"http": proxy_complete_url, "https": proxy_complete_url}
    url = 'https://httpbin.org/ip'

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, proxy=proxy_complete_url, timeout=15) as response:
                if response.status != 200:
                    return False, None
                ic(f'Proxy {proxy_complete_url} is working.')
                return True, proxy_formatted
        except (
                asyncio.TimeoutError, aiohttp.ClientError, AssertionError, OSError, RuntimeError,
                ConnectionResetError) as e:
            ic(f'Error in is_proxy_valid: {e}')
            return False, None


async def _test_proxy(session: aiohttp.ClientSession, proxy: URL, timeout: int, retries: int) -> bool:
    """
    Test a single proxy to see if it is valid.

    :param session: Aiohttp ClientSession
    :param proxy: Proxy in the format: protocol://ip:port
    :param timeout: Timeout for the request
    :param retries: Number of retries if the request fails
    :return: True if the proxy is valid, False otherwise
    """
    for attempt in range(retries + 1):
        try:
            async with session.get("https://httpbin.org/ip", proxy=str(proxy), timeout=timeout,
                                   allow_redirects=True) as response:
                if response.status == 200:
                    json_response = await response.json()
                    if json_response["origin"] == proxy.host:
                        ic(f"Valid proxy: {str(proxy)}")
                        return True
        except (aiohttp.ClientError, asyncio.TimeoutError):
            if attempt == retries:
                return False
    return False


async def test_proxies(proxies: List[ProxyDict], timeout: int = 30, retries: int = 3,
                       simultaneous_requests: int = 500) -> List[ProxyDict]:
    """
    Test a list of proxies and return the valid ones.

    :param proxies: List of ProxyDict
    :param timeout: Timeout for the request
    :param retries: Number of retries if the request fails
    :param simultaneous_requests: How many requests to make at the same time
    :return: List of valid ProxyDict
    """
    semaphore = asyncio.Semaphore(simultaneous_requests)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for proxy in proxies:
            proxy_url = proxy['url']
            task = asyncio.create_task(
                __test_proxy_with_semaphore(session, proxy_url, timeout, retries, semaphore)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        valid_proxies = [proxy for proxy, is_valid in zip(proxies, results) if is_valid]

    return valid_proxies


async def __test_proxy_with_semaphore(session: aiohttp.ClientSession, proxy: URL, timeout: int, retries: int,
                                      semaphore: asyncio.Semaphore) -> bool:
    """
    Test a proxy while respecting the semaphore limit.

    :param session: Aiohttp ClientSession
    :param proxy: Proxy in the format: protocol://ip:port
    :param timeout: Timeout for the request
    :param retries: Number of retries if the request fails
    :param semaphore: Semaphore to limit concurrent requests
    :return: True if the proxy is valid, False otherwise
    """
    async with semaphore:
        return await _test_proxy(session, proxy, timeout, retries)
