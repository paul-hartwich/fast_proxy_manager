import asyncio
from typing import List, Tuple, Dict, Any

import aiohttp
from icecream import ic


async def is_proxy_valid(proxy_complete_url: str) -> Tuple[bool, Any]:
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
