import aiohttp
from yarl import URL
import asyncio


async def http_github() -> list[URL]:
    """
    :return: List of http proxies from TheSpeedX GitHub repository.
    """
    url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/refs/heads/master/http.txt"
    protocol = "http"
    # every line is a new http proxy with the format: ip:port
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            urls = []
            for line in (await response.text()).split("\n"):
                if line:
                    urls.append(URL(f"{protocol}://{line}"))
            return urls


async def github(country, anonymity) -> list[URL]:
    """
    When just all proxies are fetched, they can still be filtered by country and anonymity.
    :return: List of http proxies from proxifly GitHub repository.
    """
    url = "https://github.com/proxifly/free-proxy-list/tree/main"
    protocol = "http"
    # every line is a new http proxy with the format: ip:port
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            urls = []
            for line in (await response.text()).split("\n"):
                if line:
                    urls.append(URL(f"{protocol}://{line}"))
            return urls


if __name__ == '__main__':
    from pprint import pprint


    async def main():
        proxies = await http_github()
        pprint(proxies)


    asyncio.run(main())
