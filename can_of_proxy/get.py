import orjson
import asyncio
from utils import URL
import aiohttp
from icecream import ic


async def get_request(url: str, retries: int = 1, timeout: int = 10,
                      proxy: URL = None, session: aiohttp.ClientSession = None
                      ) -> aiohttp.ClientResponse:
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
    created_session = False

    for attempt in range(retries):
        try:
            if session is None:
                session = aiohttp.ClientSession()
                created_session = True

            async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as response:
                return await response.text()
        except aiohttp.ClientConnectionError as e:
            ic(f"Connection closed (Attempt {attempt + 1}/{retries}): {e}")
            if attempt == retries - 1:
                raise  # Give up after max retries
            await asyncio.sleep(1)  # Wait before retrying
        finally:
            if created_session and session is not None and not session.closed:
                await session.close()


async def github_proxifly():
    url = URL("https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.json")
    response = await get_request(url, retries=3, timeout=15)

    try:
        proxies = orjson.loads(response)
        return proxies
    except orjson.JSONDecodeError:
        print("Failed to parse JSON")
        return []


if __name__ == '__main__':
    from test_speed import timer


    @timer
    async def main():
        proxies = await github_proxifly()
        ic(len(proxies))
        ic(proxies[:2])


    asyncio.run(main())
