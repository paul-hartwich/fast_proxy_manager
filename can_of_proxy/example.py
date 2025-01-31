import can_of_proxy as cop
import aiohttp
import asyncio

manager = cop.Can()

manager.fetch_proxies()

url = "https://httpbin.org/get"


async def main():
    async with aiohttp.ClientSession() as session:
        response = await manager.get_request(url, session)
        print(response)


asyncio.run(main())
