import orjson
from yarl import URL
import asyncio
from typing import List, Union
import aiohttp
from can_of_proxy.types_and_exceptions import ProxyDict
from colorama import Fore, Style


async def get_request(url: str, retries=3):
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}

    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.read()
        except aiohttp.ClientConnectionError as e:
            print(f"Connection closed (Attempt {attempt + 1}/{retries}): {e}")
            if attempt == retries - 1:
                raise  # Give up after max retries
            await asyncio.sleep(1)  # Wait before retrying


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
                        print(Fore.GREEN + f"Valid proxy: {str(proxy)}" + Style.RESET_ALL)
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


async def test_internet_connection() -> bool:
    """
    Test if there is an internet connection.

    :return: True if there is an internet connection, False otherwise
    """
    try:
        response = await get_request("https://httpbin.org/ip")
        if response.status == 200:
            return True
    except aiohttp.ClientError:
        return False


async def github_proxifly():
    url = URL("https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.json")
    response_text = await get_request(url)

    try:
        response_text = response_text.decode("utf-8")
        proxies = orjson.loads(response_text)
        return proxies
    except orjson.JSONDecodeError:
        print("Failed to parse JSON")
        return []


if __name__ == '__main__':
    from pprint import pprint
    import time


    class Timer:
        def __init__(self):
            self.start = 0
            self.end = 0

        def __enter__(self):
            self.start = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end = time.time()
            print(f"Time: {self.end - self.start}")


    timer = Timer()


    async def main():
        with timer:
            proxies = await github_proxifly()
        pprint(len(proxies))


    asyncio.run(main())
