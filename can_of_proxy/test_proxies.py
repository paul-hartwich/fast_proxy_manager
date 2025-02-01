import asyncio
from typing import Tuple, List, Union, Dict
import aiohttp
from icecream import ic
from utils import URL


async def _is_proxy_valid(proxy: Dict, supported_protocols: Tuple[str] = ('http', 'https')) -> Union[str, None]:
    """Proxy dictionary must contain 'url' or 'proxy' key or 'ip', 'port', 'protocol' keys"""
    try:
        protocol = proxy['protocol']
        url = f"{protocol}://{proxy['ip']}:{str(proxy['port'])}"
    except KeyError:
        url = proxy.get('url') or proxy.get('proxy')
        if not url:
            raise ValueError("Proxy dictionary must contain 'url' or 'proxy' key or 'ip', 'port', 'protocol' keys")
        url = URL(url)
        protocol = url.protocol

    use_ssl: bool = False
    if proxy.get('ssl') is True:
        use_ssl = True

    if protocol not in supported_protocols:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://httpbin.org/ip", proxy=url,
                                   allow_redirects=True,
                                   timeout=15,
                                   ssl=use_ssl) as response:
                if response.status == 200:
                    ic(f"Valid: {url}")
                    return url
                return None
    except (asyncio.TimeoutError, aiohttp.ClientError, AssertionError, OSError, RuntimeError,
            ConnectionResetError, aiohttp.ClientConnectionError, aiohttp.ClientHttpProxyError):
        print("Proxy is invalid")
        return None


async def get_valid_proxies(proxies: List[Dict]) -> Tuple[bool, Union[List[Dict], None]]:
    """Dict must contain 'url' key or preferably 'ip' and 'port' keys."""
    valid_proxies = []
    for proxy in proxies:
        valid = await _is_proxy_valid(proxy)
        if valid is not None:
            valid_proxies.append(valid)
            ic(f"Valid: {valid}")
    return valid_proxies


if __name__ == '__main__':
    from get import custom_json_proxy_list


    async def main():
        proxies = await custom_json_proxy_list(
            "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json")
        proxies = proxies['proxies']
        ic(len(proxies))
        proxies = await get_valid_proxies(proxies)
        ic(proxies[:2])
        ic(len(proxies))


    asyncio.run(main())
