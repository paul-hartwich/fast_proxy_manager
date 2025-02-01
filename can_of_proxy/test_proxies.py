import asyncio
from typing import Tuple, List, Union, Dict
import aiohttp
from icecream import ic
from utils import URL


class ProxyConfig:
    timeout = 15
    allow_redirects = True
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}


async def _is_proxy_valid(proxy: Dict, session: aiohttp.ClientSession,
                          supported_protocols: Tuple[str] = ('http', 'https')) -> Union[str, None]:
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

    try:
        if protocol not in supported_protocols:
            raise ValueError(f"Unsupported protocol: {protocol}")

        async with session.get("https://httpbin.org/ip", proxy=str(url), allow_redirects=ProxyConfig.allow_redirects,
                               timeout=ProxyConfig.timeout, headers=ProxyConfig.headers) as response:
            if response.status == 200:
                ic(f"Valid: {url}")
                return str(url)
            return None
    except aiohttp.ClientHttpProxyError as e:
        print(f"Proxy error: {e}")
        return None
    except aiohttp.ClientConnectionError as e:
        print(f"Connection closed: {e}")
        return None
    except asyncio.TimeoutError:
        print(f"Timeout error: {url}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    except ConnectionResetError as e:
        print(f"Connection reset error: {e}")
        return None


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
    from get import github_proxifly, custom_json_proxy_list


    async def main():
        proxies = await custom_json_proxy_list(
            "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json")
        proxies = proxies['proxies']
        ic(len(proxies))
        proxies = await get_valid_proxies(proxies)
        ic(proxies[:2])
        ic(len(proxies))


    asyncio.run(main())
