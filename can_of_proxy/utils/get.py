from typing import Optional
import json
from yarl import URL
import asyncio
from typing import List
from can_of_proxy.utils.types_and_exceptions import ProxyDict
import aiohttp


async def get_request(url: str, proxy: Optional[URL] = None,
                      session: Optional[aiohttp.ClientSession] = None) -> aiohttp.ClientResponse:
    """
    Basic GET request with aiohttp and async/await.
    """
    close_session = False  # Track if we created the session
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        async with session.get(url, proxy=proxy, allow_redirects=True) as response:
            response.raise_for_status()
            return response
    finally:
        if close_session:
            await session.close()  # Close session if we created it


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


async def github_proxifly(country: None | str = None, anonymity: None | str = None, https_over_http: bool = True) -> \
        List[URL] | List[ProxyDict]:
    """
    When just all proxies are fetched, they can still be filtered by country and anonymity.
    :return: List of http proxies from proxifly GitHub repository.

    For more:
    https://github.com/proxifly/free-proxy-list/tree/main
    """
    url = URL("https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.json")
    response = await get_request(url)
    try:
        response_text = await response.text()
        proxies = json.loads(response_text)
        return proxies
    except json.JSONDecodeError:
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
            pprint(proxies)


    asyncio.run(main())
