import asyncio
from typing import Tuple, List, Union, Dict
import aiohttp
from icecream import ic
from utils import URL


async def _is_proxy_valid(proxy: Dict, session: aiohttp.ClientSession,
                          supported_protocols: Tuple[str] = ('http', 'https')) -> Union[str, None]:
    """Proxy dictionary must contain 'url' or 'proxy' key or 'ip', 'port', 'protocol' keys"""
    try:
        protocol = proxy['protocol']
        url = URL(f"{protocol}://{proxy['ip']}:{str(proxy['port'])}")
    except KeyError:
        url = proxy.get('url') or proxy.get('proxy')
        if not url:
            raise ValueError("Proxy dictionary must contain 'url' or 'proxy' key or 'ip', 'port', 'protocol' keys")
        url = URL(url)
        protocol = url.protocol

    if protocol not in supported_protocols:
        return None

    try:
        async with session.get("https://httpbin.org/ip", proxy=repr(url), allow_redirects=True, timeout=20) as response:
            if response.status == 200:
                ic(f"Valid: {url}")
                return url
            return None
    except (asyncio.TimeoutError, aiohttp.ClientError, ConnectionResetError):
        return None


async def get_valid_proxies(proxies: List[Dict], min_working_proxies: int, max_working_proxies: int,
                            simultaneous_proxy_requests: int = 200) -> List[str]:
    """Dict must contain 'url' key or preferably 'ip' and 'port' keys."""
    valid_proxies = []
    semaphore = asyncio.Semaphore(simultaneous_proxy_requests)

    async with aiohttp.ClientSession() as session:
        async def limited_is_proxy_valid(proxy: Dict) -> Union[str, None]:
            async with semaphore:
                if len(valid_proxies) >= max_working_proxies:
                    return None
                result = await _is_proxy_valid(proxy, session)
                if result:
                    valid_proxies.append(result)
                return result

        tasks = [limited_is_proxy_valid(proxy) for proxy in proxies]
        await asyncio.gather(*tasks)

    return valid_proxies[:max_working_proxies]


if __name__ == '__main__':
    from get import custom_json_proxy_list


    async def main():
        proxies = await custom_json_proxy_list(
            "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json")
        proxies = proxies['proxies']
        ic(len(proxies))
        proxies = await get_valid_proxies(proxies, min_working_proxies=20, max_working_proxies=200)
        ic(proxies[:2])
        ic(len(proxies))


    asyncio.run(main())
