import requests
import aiohttp


def get_request(url: str, proxy: str) -> requests.Response:
    if proxy is None:
        return requests.get(url)
    return requests.get(url, proxies={'http': proxy, 'https': proxy})


def test_proxy(proxy: str) -> requests.Response:
    request = get_request("https://httpbin.org/ip", proxy)

    if request.status_code == 200 and request.json()['origin'] == proxy.split(":")[0]:
        return True
    return False
