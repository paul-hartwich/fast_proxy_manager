import aiohttp
from yarl import URL


async def http_github() -> list[URL]:
    async def get():
        url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/refs/heads/master/http.txt"
        protocol = "http"
        # every like a new http proxy with the format: ip:port
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                urls = []
                for line in (await response.text()).split("\n"):
                    if line:
                        urls.append(URL(f"{protocol}://{line}"))
                return urls

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(http_github())

if __name__ == '__main__':
    import asyncio
    from pprint import pprint
    pprint(http_github())
