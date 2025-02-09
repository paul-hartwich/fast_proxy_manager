import asyncio
import fast_proxy_manager
from functools import partial


async def main():
    proxy_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json"

    manager = fast_proxy_manager.Manager(data_file=None,
                                         fetching_method=[partial(fast_proxy_manager.Fetch.custom, proxy_url)])
    await manager.fetch_proxies(test_proxies=False)
    print(len(manager.data_manager))
    print(manager.data_manager.get_proxy())
    manager.data_manager.force_rm_last_proxy()

    for _ in range(10):
        print(manager.data_manager.get_proxy(protocol="http"))

    print(len(manager.data_manager))


asyncio.run(main())
