import asyncio
from fast_proxy_manager import partial, Manager, Fetch
import logging

logging.getLogger("fast_proxy_manager").setLevel(logging.DEBUG)


async def main():
    proxy_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"

    manager = Manager(data_file=None, fetching_method=[partial(Fetch.custom, proxy_url)])

    await manager.fetch_proxies(test_proxies=False)

    manager.get_proxy(protocol="http")


asyncio.run(main())
