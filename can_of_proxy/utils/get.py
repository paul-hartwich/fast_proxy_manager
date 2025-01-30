import aiohttp
import asyncio
from yarl import URL
from typing import List


async def test_internet_connection() -> bool:
    """
    Test if there is an internet connection.

    :return: True if there is an internet connection, False otherwise
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://httpbin.org/ip") as response:
                return response.status == 200
    except aiohttp.ClientError:
        return False


async def get_request(url: str, proxy: URL, session: aiohttp.ClientSession = None) -> aiohttp.ClientResponse:
    """
    Does not require proxy or handle exceptions.
    Basic GET request with aiohttp and async/await.

    :param session: An aiohttp ClientSession, not required but useful for performance
    :param url: URL to get
    :param proxy: Proxy to use in the format: protocol://ip:port
    :return: aiohttp ClientResponse
    """
    if session is None:
        async with aiohttp.ClientSession() as session:
            if proxy is None:
                async with session.get(url) as response:
                    return response
            else:
                async with session.get(url, proxy=proxy) as response:
                    return response
    else:
        if proxy is None:
            async with session.get(url) as response:
                return response
        else:
            async with session.get(url, proxy=proxy) as response:
                return response


async def test_proxy(session: aiohttp.ClientSession, proxy: URL, timeout: int, retries: int) -> bool:
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
            async with session.get("https://httpbin.org/ip", proxy=proxy, timeout=timeout) as response:
                if response.status == 200:
                    return True
        except (aiohttp.ClientError, asyncio.TimeoutError):
            if attempt == retries:
                return False
    return False


async def mass_testing(proxies: List[URL], timeout: int = 10, retries: int = 0, simultaneous_requests: int = 10) -> \
        List[str]:
    """
    Test a list of proxies and return the valid ones.

    :param simultaneous_requests: How many requests to make at the same time
    :param proxies: List of proxies in the format: protocol://ip:port
    :param timeout: Timeout for the request
    :param retries: Number of retries if the request fails
    :return: List of valid proxies
    """
    semaphore = asyncio.Semaphore(simultaneous_requests)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for proxy in proxies:
            task = asyncio.create_task(
                _test_proxy_with_semaphore(session, proxy, timeout, retries, semaphore)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        valid_proxies = [proxy for proxy, is_valid in zip(proxies, results) if is_valid]

    return valid_proxies


async def _test_proxy_with_semaphore(session: aiohttp.ClientSession, proxy: URL, timeout: int, retries: int,
                                     semaphore: asyncio.Semaphore) -> bool:
    """
    Test a proxy while respecting the semaphore limit.

    :param session: Aiohttp ClientSession
    :param proxy: Proxy in the format: protocol://ip:port or class IP
    :param timeout: Timeout for the request
    :param retries: Number of retries if the request fails
    :param semaphore: Semaphore to limit concurrent requests
    :return: True if the proxy is valid, False otherwise
    """
    async with semaphore:
        return await test_proxy(session, proxy, timeout, retries)


if __name__ == '__main__':
    all_proxies = ["http://proxy1:port", "http://proxy2:port", ...]
    working_proxies = asyncio.run(mass_testing(all_proxies, timeout=10, retries=2, simultaneous_requests=5))
    print(working_proxies)
