import asyncio
from typing import Tuple, List, Union, Dict
import aiohttp
from icecream import ic
from utils import ProxyDict
import utils
from random import shuffle


async def _is_proxy_valid(proxy: ProxyDict, session: aiohttp.ClientSession,
                          supported_protocols: Tuple[str] = ('http', 'https')) -> Union[ProxyDict, None]:
    """Proxy dictionary must contain 'url' or 'proxy' key or 'ip', 'port', 'protocol' keys"""
    url = proxy["url"]
    protocol = url.protocol

    if protocol not in supported_protocols:
        return None

    try:
        async with session.get("https://httpbin.org/ip", proxy=repr(url), allow_redirects=True, timeout=20) as response:
            if response.status == 200:
                ic(f"Valid: {url}")
                return proxy
            return None
    except (asyncio.TimeoutError, aiohttp.ClientError, ConnectionResetError):
        return None


async def get_valid_proxies(proxies: List[ProxyDict], max_working_proxies: Union[int, False] = False,
                            simultaneous_proxy_requests: int = 200) -> List[ProxyDict]:
    """Dict must contain 'url' key or preferably 'ip' and 'port' keys."""
    valid_proxies = []
    if not all(isinstance(proxy, dict) for proxy in proxies):
        raise ValueError("All items in the proxies list must be dictionaries")
    shuffle(proxies)
    semaphore = asyncio.Semaphore(simultaneous_proxy_requests)

    async with aiohttp.ClientSession() as session:
        async def limited_is_proxy_valid(proxy: Dict) -> Union[ProxyDict, None]:
            async with semaphore:
                if max_working_proxies and len(valid_proxies) >= max_working_proxies:
                    return None
                result = await _is_proxy_valid(proxy, session)
                if result:
                    valid_proxies.append(result)
                return result

        tasks = [limited_is_proxy_valid(proxy) for proxy in proxies]
        await asyncio.gather(*tasks)

    return valid_proxies[:max_working_proxies] if max_working_proxies else valid_proxies


if __name__ == '__main__':
    from get import fetch_github_proxifly, fetch_json_proxy_list


    async def main():
        proxies = await fetch_json_proxy_list(
            "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json")
        proxies = utils.convert_to_proxy_dict_format(proxies)
        ic(len(proxies))
        proxies = await get_valid_proxies(proxies, max_working_proxies=20)
        ic(proxies[:5])
        ic(len(proxies))


    asyncio.run(main())
