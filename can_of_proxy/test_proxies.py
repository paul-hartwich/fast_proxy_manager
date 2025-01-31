from typing import Tuple, List, Union, Dict
import asyncio
import aiohttp
from icecream import ic
from utils import URL


async def _is_proxy_valid(proxy: Dict, session: aiohttp.ClientSession) -> Tuple[bool, Union[str, None]]:
    """Dict must contain 'url' key or preferably 'ip' and 'port' keys."""
    try:
        url = proxy['ip'] + ':' + str(proxy['port'])
    except KeyError:
        url = URL(proxy['url'])
        url = url.ip + ':' + url.port

    try:
        async with session.get("https://httpbin.org/ip", proxy=url) as response:
            if response.status == 200:
                return True, url
            else:
                return False, None
    except aiohttp.ClientConnectionError as e:
        ic(f"Connection closed: {e}")
        return False, None


async def get_valid_proxies(proxies: List[Dict]) -> Tuple[bool, Union[List[Dict], None]]:
    """Dict must contain 'url' key or preferably 'ip' and 'port' keys."""
    valid_proxies = []
    async with aiohttp.ClientSession() as session:
        for proxy in proxies:
            valid, formatted_proxy = await _is_proxy_valid(proxy, session)
            if valid:
                valid_proxies.append(formatted_proxy)
                ic(f"Valid: {formatted_proxy}")
        return True, valid_proxies


if __name__ == '__main__':
    from get import github_proxifly


    async def main():
        proxies = await github_proxifly()
        ic(len(proxies))
        proxies = await get_valid_proxies(proxies)


    asyncio.run(main())
