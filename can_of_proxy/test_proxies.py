import asyncio
from typing import Tuple, Any
from utils import URL
import aiohttp
from icecream import ic


async def is_proxy_valid(proxy: URL) -> Tuple[bool, Any]:
    url = f"{proxy.ip}:{proxy.port}"
    proxy_formatted = {"http": url, "https": url}
    dest_url = 'https://httpbin.org/ip'

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(dest_url, proxy=proxy_formatted, timeout=15) as response:
                if response.status != 200:
                    return False, None
                ic(f'Proxy {url} is working.')
                return True, proxy_formatted
        except (
                asyncio.TimeoutError, aiohttp.ClientError, AssertionError, OSError, RuntimeError,
                ConnectionResetError) as e:
            ic(f'Error in is_proxy_valid: {e}')
            return False, None


if __name__ == '__main__':
    from get import github_proxifly


    async def main():
        proxies = await github_proxifly()
        valid_proxies = []
        for proxy in proxies:
            valid, formatted_proxy = await is_proxy_valid(proxy)
            if valid:
                valid_proxies.append(formatted_proxy)
        ic(valid_proxies)


    asyncio.run(main())
