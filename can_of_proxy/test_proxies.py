import asyncio
from typing import Tuple, List, Union, Dict
import aiohttp
from icecream import ic
from utils import URL


class ProxyConfig:
    timeout = 15
    retries = 3


async def _is_proxy_valid(proxy: Dict, session: aiohttp.ClientSession) -> Tuple[bool, Union[str, None]]:
    """Proxy dictionary must contain 'url' or 'proxy' key or 'ip', 'port', 'protocol' keys"""
    try:
        url = f"{proxy['protocol']}://{proxy['ip']}:{str(proxy['port'])}"
    except KeyError:
        url = proxy.get('url') or proxy.get('proxy')
        if not url:
            raise ValueError("Proxy dictionary must contain 'url' or 'proxy' key or 'ip', 'port', 'protocol' keys")
        url = URL(url)

    try:
        async with session.get("https://httpbin.org/ip", proxy=str(url), allow_redirects=True,
                               timeout=ProxyConfig.timeout) as response:
            if response.status == 200:
                ic(f"Valid: {url}")
                return True, str(url)
            else:
                ic(f"Invalid: {url}")
                return False, None
    except aiohttp.ClientHttpProxyError as e:
        ic(f"Proxy error: {e}")
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
        ic(proxies[:2])


    asyncio.run(main())
