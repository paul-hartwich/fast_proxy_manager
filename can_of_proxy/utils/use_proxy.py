import aiohttp
import asyncio


async def get_request(url: str, proxy: str) -> aiohttp.ClientResponse:
    async with aiohttp.ClientSession() as session:
        if proxy is None:
            async with session.get(url) as response:
                return response
        else:
            async with session.get(url, proxy=proxy) as response:
                return response


async def test_proxy(proxy: str) -> bool:
    try:
        response = await get_request("https://httpbin.org/ip", proxy)
        if response.status == 200:
            data = await response.json()
            # Validate if the IP matches the proxy's IP
            if data.get('origin') == proxy.split(":")[0]:
                return True
    except Exception as e:
        print(f"Error testing proxy: {e}")
    return False


# Example usage
async def main():
    proxy = "http://your_proxy_ip:your_proxy_port"
    is_valid = await test_proxy(proxy)
    print(f"Proxy valid: {is_valid}")


if __name__ == '__main__':
    asyncio.run(main())
