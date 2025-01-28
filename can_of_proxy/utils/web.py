import aiohttp
import asyncio


async def get_request(url: str, proxy: str) -> aiohttp.ClientResponse:
    """
    Does not require proxy or handle exceptions.
    Basic GET request with aiohttp and async/await.

    :param url: URL to get
    :param proxy: Proxy to use in the format: protocol://ip:port
    """

    async with aiohttp.ClientSession() as session:
        if proxy is None:
            async with session.get(url) as response:
                return response
        else:
            async with session.get(url, proxy=proxy) as response:
                return response


async def mass_testing(proxies: list[str], timeout: int = 10, retries: int = 0) -> list[str]:
    """
    Test a list of proxies and return the valid ones.

    :param proxies: List of proxies in the format: protocol://ip:port
    :param timeout: Timeout for the request
    :param retries: Number of retries if the request fails
    :return: List of valid proxies
    """
    valid_proxies = []
    for proxy in proxies:
        is_valid = await test_proxy(proxy, timeout, retries)
        if is_valid:
            valid_proxies.append(proxy)
    return valid_proxies


async def test_proxy(proxy: str, timeout: int = 10, retries: int = 0) -> bool:
    try:
        response = await get_request("https://httpbin.org/ip", proxy)
        if response.status == 200:
            data = await response.json()
            # Validate if the IP matches the proxy's IP
            if data.get('origin') == proxy.split(":")[0]:
                return True
    except Exception as e:
        print(f"Error testing proxy: {e}")
    return False


if __name__ == '__main__':
    async def main():
        proxy = "http://78.46.225.37:19051"
        is_valid = await test_proxy(proxy)
        print(f"Proxy valid: {is_valid}")


    asyncio.run(main())
